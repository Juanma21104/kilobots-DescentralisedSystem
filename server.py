from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from model import KilobotFormationModel
from constant import State, KILOBOTS_X, KILOBOTS_Y, GRID_SIZE, SEPARATION

# --- VISUALIZATION ---
def agent_portrayal(agent):
    if agent.state == State.SR1A_ID_ASSIGNMENT:
        text = agent.my_id
    elif agent.state == State.SR2A_ORIGIN_ASSIGNMENT:
        text = str(agent.numOriginAssigment)
    elif agent.state == State.SR2A_ORIGIN_SET_POSITION:
        text = str(agent.position)
    elif agent.state == State.SR2B_SET_REC_DIMENSION:
        text = str(agent.count)
    elif agent.state == State.SR2B_SET_RELATIVE_POS:
        text = str(agent.position) if agent.position else ""
    elif agent.state == State.SR2C_SET_GLOBAL_POS:
        text = str(agent.position) if agent.position else ""
    elif agent.state == State.SET_ANIMATION_SINCRONIZATION or agent.state == State.SET_ROLE_COLOR:
        text = ""
    else:
        text = str(len(agent.neighbor_ids)) if (len(agent.neighbor_ids)) > 0 else ""
    return { # Properties of robots for visualization
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "Color": agent.led_color,
        "r": 0.8,
        "text": text, 
        "text_color": "white"
    }


canvas_width = KILOBOTS_X * SEPARATION
canvas_height = KILOBOTS_Y * SEPARATION

pixel_width = canvas_width * GRID_SIZE
pixel_height = canvas_height * GRID_SIZE
grid = CanvasGrid(agent_portrayal, canvas_width, canvas_height, pixel_width, pixel_height)


server = ModularServer(
    KilobotFormationModel,
    [grid],
    "Kilobots"
)

server.port = 8521

if __name__ == "__main__":
    server.launch()