import random
from module import ResponsiveModule
from environment import Environment
from engine import SimulationEngine

# Set random seed for reproducibility
random.seed(42)

if __name__ == "__main__":
    # Define the environment bounds as (min_x, min_y, max_x, max_y).
    env = Environment(bounds=(0, 0, 100, 100))
    
    # Create a few modules with specified width and height.
    for i in range(8):
        # Place modules in a random location with some margin from the edge.
        pos = (random.randint(20, 80), random.randint(20, 80))
        module = ResponsiveModule(module_id=i, position=(int(pos[0]), int(pos[1])), width=random.randint(5, 20), height=random.randint(5, 20))
        env.add_module(module)
        
    engine = SimulationEngine(environment=env)
    engine.run(steps=100, plot=True, plot_overlap=True, plot_outside=True, plot_action_history=True, pause_time=0.2)
