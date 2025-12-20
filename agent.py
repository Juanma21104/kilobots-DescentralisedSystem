from mesa import Agent
import numpy as np
import random, math
from constant import State
from routines import RoutineR1, RoutineR2, RoutineR3

class Kilobot(Agent, RoutineR1, RoutineR2, RoutineR3):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.state = State.SR1A_ID_ASSIGNMENT # Initial state
        self.messages_sent_count = 0
        self.led_color = "grey"   # Initial color
        self.role = "UNDECIDED"   # Roles: CORNER, BORDER, MIDDLE
        self.isBroken = False  # Determine if the kilobot is broken at initialization
        self.neighbors_count = 0  # Number of neighbors
        self.inbox = []           # Inbox for messages
        self.internal_clock = 0   # Internal clock for timing phases
        self.my_id = random.randint(1, 255)         # Initial random ID
        self.randomNumber = random.randint(0, 255)  # Random number for ID conflict resolution
        self.neighbor_counts = {}  # Dict to store neighbor ID -> count
        self.neighbor_ids = []     # List of neighbor IDs
        self.neighbor_ids_randomNum = [] # List of neighbor IDs and their random numbers
        self.neighbor_roles = []   # Dict to store neighbor ID -> role
        self.neighbor_positions = [] # List of neighbor positions
        self.blacklist_ids = []    # IDs to avoid in SR1a
        self.min_dist_seen = 9999  # Minimum distance seen in SR1b
        self.numOriginAssigment = 999999  # Number to determine the [1,1] corner 
        self.position = []      # Global position [x,y]
        self.count = 0          # Count for rectangle dimension setting
        self.messageFromCorner = False # Flag to indicate message from corner received
        self.countMessage = {"count": 0, "C1": 0, "C2": 0, "C3": 0} # Message for rectangle dimension
        self.sentCount = False  # Flag to avoid resending count message
        self.countFullMessage = None  # Full count message for global position setting
        self.sentFullCount = False    # Flag to avoid resending full count message
        self.auxPosition = [-1,-1]    # Auxiliary position for global position setting

        

    # Every robots' step consists of two phases: sending (step) and resolution (advance)
    def step(self):
        """
        Step 1: Sending phase (broadcast presence)
        Each robot sends its "IR" message to neighbors
        """

        if self.internal_clock % 150 == 100:
            # Simulate possible failure
            if random.random() < self.model.failure_prob:
                self.isBroken = True
        if self.isBroken:
            self.led_color = "brown" # Dead kilobot color
            return  # Broken kilobots do nothing

        self.internal_clock += 1
        self.broadcast_presence()

    def advance(self):
        """
        Step 2: Resolution phase
        All robots read their inbox and decide what to do
        """

        if self.isBroken:
            return  # Broken kilobots do nothing

        # Simulated timers for phase transitions

        # ROUTINE R1
        if self.internal_clock == 1:
            self.state = State.SR1A_ID_ASSIGNMENT # Assign IDs (SR1a)
            self.led_color = "grey"

        elif self.internal_clock == 60:
            self.state = State.SR1B_NEIGHBOR_LIST # Create neighbor list (SR1b)
            self.led_color = "lightblue"
            
        elif self.internal_clock == 140:
            self.state = State.SR1C_ROLE_ID # Collect neighbor counts (SR1c phase 1)
            self.led_color = "orange"
            
        elif self.internal_clock == 180:
            self.state = State.SR1C_SET_ROLE # Determine role (SR1c phase 2)

        # ROUTINE R2
        elif self.internal_clock == 260:
            self.state = State.SR2A_ORIGIN_ASSIGNMENT # Send assignment numbers from the corners (SR2a phase 1)
            self.led_color = "grey"

        elif self.internal_clock == 320:
            self.state = State.SR2A_SET_ORIGIN        # The lower corner number becomes [1,1] (SR2a phase 2)

        elif self.internal_clock == 370:
            self.state = State.SR2A_ORIGIN_SET_POSITION # [1,1] sends positions to BORDER and MIDDLE neighbors (SR2a phase 3)

        elif self.internal_clock == 400:
            self.state = State.SR2B_SET_REC_DIMENSION # BORDER and CORNER has done the counting (SR2b phase 1)

        elif self.internal_clock == 970:
            self.state = State.SR2B_SET_RELATIVE_POS  # BORDER and CORNER set their positions (SR2b phase 2)
            self.led_color = "grey"

        elif self.internal_clock == 1070:
            self.state = State.SR2C_SET_GLOBAL_POS # All robots set their global positions (SR2c)

        # ROUTINE R3
        elif self.internal_clock == 1270:
            self.state = State.SET_ANIMATION_SINCRONIZATION # Synchronize animation
            
        elif self.internal_clock == 1300:
            self.state = State.SET_ROLE_COLOR  # Every robot sets its role according to its position


        # --- Execution of each subroutine's logic --- 
        # Depending on the current state, execute the corresponding logic
        if self.state == State.SR1A_ID_ASSIGNMENT:
            self.run_sr1a()

        elif self.state == State.SR1B_NEIGHBOR_LIST:
            self.run_sr1b()

        elif self.state == State.SR1C_ROLE_ID:
            self.run_sr1c_collection()

        elif self.state == State.SR1C_SET_ROLE:
            self.determine_role()

        elif self.state == State.SR2A_ORIGIN_ASSIGNMENT:
            self.run_sr2a_origin_assignment()

        elif self.state == State.SR2A_SET_ORIGIN:
            self.setOriginAssignment()

        elif self.state == State.SR2A_ORIGIN_SET_POSITION:
            self.setOriginNeighborsPosition()

        elif self.state == State.SR2B_SET_REC_DIMENSION:
            self.setRecDimension()

        elif self.state == State.SR2B_SET_RELATIVE_POS:
            self.set_relative_position()

        elif self.state == State.SR2C_SET_GLOBAL_POS:
            self.set_global_position()

        elif self.state == State.SET_ANIMATION_SINCRONIZATION:
            self.set_animation_sincronization()

        elif self.state == State.SET_ROLE_COLOR:
            self.set_role_color()
            
        # Clear inbox after processing
        self.inbox = []


    
    # ---------------------------------------------------------
    # AUXILIARY METHODS
    # --------------------------------------------------------- 

    def check_position(self, neighbors_positions):
        """Check if I can determine coordinates x or y based on neighbors' positions"""

        if len(neighbors_positions) < 3:
            return self.auxPosition

        # Separate and sort unique values of X and Y
        xs = sorted(set(p[0] for p in neighbors_positions))
        ys = sorted(set(p[1] for p in neighbors_positions))

        # Search for 3 consecutive values in X
        for i in range(len(xs) - 2):
            if xs[i+1] == xs[i] + 1 and xs[i+2] == xs[i] + 2:
                if xs[i+1] != -1:
                    self.auxPosition[0] = xs[i+1]
                    break

        # Search for 3 consecutive values in Y
        for i in range(len(ys) - 2):
            if ys[i+1] == ys[i] + 1 and ys[i+2] == ys[i] + 2:
                if ys[i+1] != -1:
                    self.auxPosition[1] = ys[i+1]
                    break


    def filter_neighbors_message(self):
        """Filter neighbors messages"""

        filtered_messages = []
        for msg in self.inbox:
            id = msg['sender_id']
            if id in self.neighbor_ids:
                filtered_messages.append(msg)
        
        return filtered_messages


    # ---------------------------------------------------------
    # Sending message method
    # ---------------------------------------------------------

    def broadcast_presence(self):
        """Simulate sending IR message to nearby neighbors"""

        # Radius 3, Moore=True (includes diagonals)
        # Simulate Kilobot's IR range, it can hear robots up to 3 units away, it can be increased if it's needed
        # because we filter distances later
        neighbors = self.model.grid.get_neighbors(
            self.pos, moore=True, include_center=False, radius=3
        )
        
        # The content of the message depends on the current state
        content = None
        if self.state == State.SR1A_ID_ASSIGNMENT:
            # In SR1a, send my ID, randomNumber, and list of neighbors heard so far
            content = {"sender_id": self.my_id, "randomNumber": self.randomNumber, "neighbors": self.neighbor_ids_randomNum}

        elif self.state == State.SR1B_NEIGHBOR_LIST:
            # In SR1b, just send my ID
            content = self.my_id

        elif self.state == State.SR1C_ROLE_ID:
            # In SR1c, send the count of my neighbors
            content = len(self.neighbor_ids)
        
        elif self.state == State.SR1C_SET_ROLE:
            content = {"id": self.my_id, "role": self.role}

        elif self.state == State.SR2A_ORIGIN_ASSIGNMENT or self.state == State.SR2A_SET_ORIGIN:
            # In SR2a (first and second phases), send my assigned number
            if self.role == "CORNER" and self.numOriginAssigment == 999999:
                randomNum = random.randint(0, 200000)
                self.numOriginAssigment = randomNum
            content = self.numOriginAssigment

        elif self.state == State.SR2A_ORIGIN_SET_POSITION:
            # In SR2a (third phase), [1,1] sends positions to BORDER and MIDDLE neighbors

            if self.led_color == "black" and self.position == [1,1]: # Origin only sends messages to its neighbors
                border_neighbors = []
                content = []
                middle_neighbors = []
                
                for n in self.neighbor_roles: # Identify BORDER and MIDDLE neighbors
                    if n['id'] in self.neighbor_ids and n['role'] == "BORDER":
                        border_neighbors.append(n)
                    elif n['id'] in self.neighbor_ids and n['role'] == "MIDDLE":
                        middle_neighbors.append(n)

                if len(border_neighbors) < 2 or len(middle_neighbors) < 1:
                    return

                # Border neighbor with lower ID gets position [2,1], other gets [1,2], middle neighbor gets [2,2]
                if border_neighbors[0]['id'] > border_neighbors[1]['id']:
                    content = [{"id": border_neighbors[1]['id'], "position": [2,1]}, {"id": border_neighbors[0]['id'], "position": [1,2]}, {"id": middle_neighbors[0]['id'], "position": [2,2]}]
                else:
                    content = [{"id": border_neighbors[0]['id'], "position": [2,1]}, {"id": border_neighbors[1]['id'], "position": [1,2]}, {"id": middle_neighbors[0]['id'], "position": [2,2]}]


                msg = {
                    "sender_id": self.my_id,
                    "content": content
                }

                for n in neighbors:
                    n.receive_message(msg)

            return  
        
        elif self.state == State.SR2B_SET_REC_DIMENSION:

            # 2 Phases:
            
            # First phase: prepare the message
            # Initial count robot [2,1] send message with count = 2 ([1,1] will be count=1), C1 = 0, C2 = 0, C3 = 0
            if self.position == [2,1] and self.role == "BORDER" and self.count == 0:
                content = {"count": 2, "C1": 0, "C2": 0, "C3": 0}
                self.count = 2
            
            # If I am BORDER, I have count (I have received it) and I have not sent it yet, I send it to my neighbors
            if self.count > 0 and self.role == "BORDER":
                content = {"count": self.count, "C1": self.countMessage['C1'], "C2": self.countMessage['C2'], "C3": self.countMessage['C3']}
            
            # If I am CORNER, I have count (I have received it) and I have not sent it yet, I send it to my neighbors
            if self.count > 0 and self.role == "CORNER" and not self.position:
                # Update C1, C2, C3 in order, if they are 0
                if self.countMessage['C1'] == 0:
                    self.countMessage['C1'] = self.count
                elif self.countMessage['C2'] == 0 and self.count != self.countMessage['C1']:
                    self.countMessage['C2'] = self.count
                elif self.countMessage['C3'] == 0 and self.count != self.countMessage['C1'] and self.count != self.countMessage['C2']:
                    self.countMessage['C3'] = self.count
                content = {"count": self.count, "C1": self.countMessage['C1'], "C2": self.countMessage['C2'], "C3": self.countMessage['C3']}

            # Second phase: send the message to appropriate neighbors
            # If I am CORNER and I have count and I have not sent it yet, I send it to my neighbors
            if self.role == "CORNER" and self.count > 0 and not self.position:
                for n in neighbors:
                    n.receive_message({
                        "sender_id": self.my_id,
                        "content": content
                    })
            
            # Otherwise, if I am BORDER and I have count and I have not sent it yet, I send it to my BORDER or CORNER neighbors
            if self.role == "BORDER" and self.count > 0:
                
                isCornerNeighbor = False
                corner_id = -1
                for robot in self.neighbor_roles:
                    if robot['role'] == "CORNER":
                        isCornerNeighbor = True
                        corner_id = robot['id']
                
                if isCornerNeighbor and self.position != [2,1] and not self.messageFromCorner:
                    content = {"corner_id": corner_id, "count": self.count, "C1": self.countMessage['C1'], "C2": self.countMessage['C2'], "C3": self.countMessage['C3']}
                else:
                    content = {"count": self.count, "C1": self.countMessage['C1'], "C2": self.countMessage['C2'], "C3": self.countMessage['C3']}
    
                for n in neighbors:
                    n.receive_message({
                        "sender_id": self.my_id,
                        "content": content
                    })
            
            return
    
        elif self.state == State.SR2B_SET_RELATIVE_POS:

            # If a robot have countFullMessage, it sends it to its neighbors
            if not (self.countFullMessage is None):
                content = self.countFullMessage
                for n in neighbors:
                    n.receive_message({
                        "sender_id": self.my_id,
                        "content": content
                    })
            
            return

        elif self.state == State.SR2C_SET_GLOBAL_POS:

            # If I have my position, send it
            if self.position:
                content = self.position
            
            # If I don't have my position, but my auxPosition is set, send auxPosition
            if not self.position and (self.auxPosition[0] != -1 or self.auxPosition[1] != -1):
                content = self.auxPosition             


        elif self.state == State.SET_ANIMATION_SINCRONIZATION or self.state == State.SET_ROLE_COLOR:
            return # No longer sending anything
        
        for n in neighbors:
            # Simulate distance calculation for SR1b
            dist = self.calculate_distance(n)
            
            msg = {
                "sender_id": self.my_id,
                "content": content,
                "dist": dist
            }
            n.receive_message(msg)


    def calculate_distance(self, other_agent):
        """Calculate Euclidean distance to another agent to simulate IR distance measurement with error"""

        dx = self.pos[0] - other_agent.pos[0]
        dy = self.pos[1] - other_agent.pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        error = np.random.normal(0, self.model.ir_error)
        dist_with_error = dist + error
        return  dist_with_error

    def receive_message(self, message):
        if random.random() > self.model.lost_message_prob:
            self.messages_sent_count += 1
            self.inbox.append(message)