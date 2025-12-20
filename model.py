from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agent import Kilobot
from constant import KILOBOTS_X, KILOBOTS_Y, SEPARATION, FAILURE_PROB, IR_ERROR, LOST_MESSAGE_PROB

# --- AUXILIAR FUNCTIONS ---

def compute_accuracy(model):
    """
    Calculates accuracy by checking the 8 possible valid coordinate system formations
    (4 possible Corners * 2 Axis orientations per corner).
    Returns the best accuracy found among the 8 hypotheses.
    """
    functional_agents = [a for a in model.schedule.agents if not a.isBroken]
    
    # If all died or there are no agents, accuracy 0
    if not functional_agents:
        return 0.0

    # Expected dimensions of the logical grid
    W = model.num_kilobots_x
    H = model.num_kilobots_y
    
    # We use the separation stored in the model
    sep = model.model_separation

    # Step 1: Collect data. 
    # List of tuples: ( (Real_X, Real_Y), (Calc_X, Calc_Y) )
    data = []
    for agent in functional_agents:
        # Convert physical position (float) to 1-based matrix index
        # Use int(round()) to avoid floating point errors at edges
        rx = int(agent.pos[0] / sep) + 1
        ry = int(agent.pos[1] / sep) + 1
        
        # Position the agent believes it has
        cx = agent.position[0] if agent.position else -1
        cy = agent.position[1] if agent.position else -1
        
        data.append(((rx, ry), (cx, cy)))

    # Step 2: Define the 8 transformations (Coordinate hypotheses)
    # r[0] is real X, r[1] is real Y.
    transforms = [
        # --- GROUP A: ALIGNED AXES ---
        lambda r: (r[0], r[1]),                     # 1. Origin Bottom-Left (Original)
        lambda r: (r[0], H - r[1] + 1),             # 2. Vertical Mirror (Origin Top-Left)
        lambda r: (W - r[0] + 1, r[1]),             # 3. Horizontal Mirror (Origin Bottom-Right)
        lambda r: (W - r[0] + 1, H - r[1] + 1),     # 4. 180 Rotation (Origin Top-Right)
        
        # --- GROUP B: TRANSPOSED AXES (90 degree rotations) ---
        lambda r: (r[1], r[0]),                     # 5. Transpose
        lambda r: (H - r[1] + 1, r[0]),             # 6. 90 Rotation
        lambda r: (r[1], W - r[0] + 1),             # 7. -90 Rotation
        lambda r: (H - r[1] + 1, W - r[0] + 1)      # 8. Inverse Transpose
    ]

    max_accuracy = 0.0

    # Step 3: Test all and keep the best one
    for t in transforms:
        correct_count = 0
        for real_pos, calc_pos in data:
            # Calculate where the robot SHOULD be according to this hypothesis
            expected = t(real_pos)
            
            # Compare with where it believes it is
            if expected[0] == calc_pos[0] and expected[1] == calc_pos[1]:
                correct_count += 1
        
        current_acc = correct_count / len(functional_agents)
        
        if current_acc > max_accuracy:
            max_accuracy = current_acc
            
        # Optimization: If we find 100%, stop
        if max_accuracy == 1.0:
            break

    return max_accuracy


def compute_avg_error(model):
    """
    Calculates the average error (Manhattan Distance) of the robots.
    """
    total_error = 0
    count = 0
    sep = model.model_separation
    
    for agent in model.schedule.agents:
        if agent.isBroken: continue
        if not agent.position or agent.position == [-1, -1]: continue

        real_grid_x = int(agent.pos[0] / sep) + 1
        real_grid_y = int(agent.pos[1] / sep) + 1
        
        calc_x = agent.position[0]
        calc_y = agent.position[1]
        
        dist = abs(real_grid_x - calc_x) + abs(real_grid_y - calc_y)
        total_error += dist
        count += 1
        
    return total_error / count if count > 0 else 0.0

def compute_avg_messages(model):
    """
    Calculates the average messages sent per robot.
    """
    total_msgs = 0
    count = 0
    for agent in model.schedule.agents:
        if not agent.isBroken:
            total_msgs += getattr(agent, 'messages_sent_count', 0)
            count += 1
    return total_msgs / count if count > 0 else 0.0


# --- MODEL CLASS ---

class KilobotFormationModel(Model):

    def __init__(self, side_length=10, 
                 failure_prob=FAILURE_PROB, ir_error=IR_ERROR,
                 lost_message_prob=LOST_MESSAGE_PROB):
        
        super().__init__()
        
        # Configure square dimensions
        """self.num_kilobots_x = side_length
        self.num_kilobots_y = side_length"""

        self.num_kilobots_x = KILOBOTS_X
        self.num_kilobots_y = KILOBOTS_Y
        
        # Store parameters
        self.failure_prob = failure_prob
        self.ir_error = ir_error
        self.lost_message_prob = lost_message_prob
        self.model_separation = SEPARATION 
        
        # Physical Grid dimensions
        self.grid_w = self.num_kilobots_x * SEPARATION
        self.grid_h = self.num_kilobots_y * SEPARATION
        
        self.grid = MultiGrid(self.grid_w, self.grid_h, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.running = True
        self.convergence_step = -1
        
        # Agent creation
        count = 0
        for i in range(self.num_kilobots_x):
            for j in range(self.num_kilobots_y):
                a = Kilobot(count, self)
                self.schedule.add(a)
                x = i * SEPARATION
                y = j * SEPARATION
                if x < self.grid_w and y < self.grid_h:
                    self.grid.place_agent(a, (x, y))
                count += 1
        
        # DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Accuracy": compute_accuracy,          
                "Avg_Error": compute_avg_error,        
                "Convergence_Time": lambda m: m.convergence_step,
                "Avg_Messages": compute_avg_messages
            }
        )

    def step(self):
        self.schedule.step()
        
        # --- Convergence detection logic ---
        if self.convergence_step == -1:
            total_agents = 0
            ready_agents = 0
            
            for agent in self.schedule.agents:
                if not agent.isBroken:
                    total_agents += 1
                    # Considered ready if it has a valid position
                    if agent.position and agent.position != [-1, -1]:
                        ready_agents += 1
            
            # If all living agents have a position
            if total_agents > 0 and ready_agents == total_agents:
                self.convergence_step = self.schedule.steps

        # Collect data passing the model as an argument
        self.datacollector.collect(self)