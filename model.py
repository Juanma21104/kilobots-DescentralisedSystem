from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from agent import Kilobot
from constant import KILOBOTS_X, KILOBOTS_Y, SEPARATION

class KilobotFormationModel(Model):
    def __init__(self):
        super().__init__()
        
        self.grid_w = KILOBOTS_X * SEPARATION
        self.grid_h = KILOBOTS_Y * SEPARATION
        
        self.grid = MultiGrid(self.grid_w, self.grid_h, torus=False)
        
        self.schedule = SimultaneousActivation(self)
        self.running = True

        count = 0
        
        for i in range(KILOBOTS_X):
            for j in range(KILOBOTS_Y):
                
                a = Kilobot(count, self)
                self.schedule.add(a)
                
                x = i * SEPARATION
                y = j * SEPARATION

                if x < self.grid_w and y < self.grid_h:
                    self.grid.place_agent(a, (x, y))
                
                count += 1

    def step(self):
        self.schedule.step()