import random
import matplotlib.pyplot as plt

class ResponsiveModule:
    def __init__(self, module_id, position, width=10, height=10):
        """
        Initialize a responsive module.
        
        Parameters:
          module_id: Unique identifier.
          position: Tuple (x, y) representing the module center.
          width: The width of the module.
          height: The height of the module.
        """
        self.module_id = module_id
        self.position = (int(round(position[0])), int(round(position[1])))  # Center (x, y)
        self.width = width
        self.height = height
        self.orientation = 0  # Unused in this simple example but available for future extension

    def evaluate_conditions(self, environment):
        """
        Check the module's bounding box relative to the environment boundaries.
        If any edge is within a defined margin to the boundary, return the necessary action
        to move the module away.
        
        Returns:
          A dictionary with keys as the action names ('move_right', 'move_left', 'move_up', 'move_down')
          and values as the distance the module should move.
        """
        min_x, min_y, max_x, max_y = environment.bounds
        x, y = self.position

        # Calculate module boundaries assuming position is at the center.
        left = x - self.width / 2
        right = x + self.width / 2
        bottom = y - self.height / 2
        top = y + self.height / 2

        margin = 10  # Threshold margin before the module starts to adjust its position
        actions_needed = {}

        if left - min_x < margin:
            actions_needed['move_right'] = margin - (left - min_x)
        elif max_x - right < margin:
            actions_needed['move_left'] = margin - (max_x - right)
        
        if bottom - min_y < margin:
            actions_needed['move_up'] = margin - (bottom - min_y)
        elif max_y - top < margin:
            actions_needed['move_down'] = margin - (max_y - top)

        return actions_needed

    def perform_actions(self, actions):
        """
        Update the module's position based on the provided actions.
        Here we assume a standard Cartesian coordinate system:
          - Increasing x moves right.
          - Increasing y moves up.
        """
        x, y = self.position
        if 'move_right' in actions:
            x += actions['move_right']
        if 'move_left' in actions:
            x -= actions['move_left']
        if 'move_up' in actions:
            y += actions['move_up']
        if 'move_down' in actions:
            y -= actions['move_down']
        # Ensure integer positions
        self.position = (int(round(x)), int(round(y)))
        print(f"Module {self.module_id} moved to position {self.position}")

    def evaluate_free_space(self, environment):
        """
        Evaluate the largest axis-aligned rectangle centered at the module's position
        that does not intersect with any other module in the environment.
        Returns (min_x, min_y, max_x, max_y) of the free rectangle.
        """
        x, y = self.position
        min_env_x, min_env_y, max_env_x, max_env_y = environment.bounds

        # Start with environment bounds
        left = min_env_x
        right = max_env_x
        bottom = min_env_y
        top = max_env_y

        for other in environment.modules:
            if other is self:
                continue
            ox, oy = other.position
            o_left = ox - other.width / 2
            o_right = ox + other.width / 2
            o_bottom = oy - other.height / 2
            o_top = oy + other.height / 2

            # If the other module overlaps horizontally with this y, it may restrict left/right
            if o_bottom < y < o_top or (y == o_bottom or y == o_top):
                if o_right <= x and o_right > left:
                    left = o_right
                if o_left >= x and o_left < right:
                    right = o_left
            # If the other module overlaps vertically with this x, it may restrict top/bottom
            if o_left < x < o_right or (x == o_left or x == o_right):
                if o_top <= y and o_top > bottom:
                    bottom = o_top
                if o_bottom >= y and o_bottom < top:
                    top = o_bottom

        return (left, bottom, right, top)

    def center_in_free_space(self, environment):
        """
        Center the module within its free space as determined by evaluate_free_space.
        Updates the module's position.
        """
        left, bottom, right, top = self.evaluate_free_space(environment)
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        # Ensure integer positions
        self.position = (int(round(center_x)), int(round(center_y)))
        print(f"Module {self.module_id} centered to position {self.position}")

    def check_overlap_and_resolve(self, environment):
        """
        Check for overlaps with other modules and move away to reduce overlap.
        Moves the module by 1 unit in the direction away from the overlapping module's center.
        Returns True if a move was made, False otherwise.
        """
        moved = False
        x, y = self.position
        for other in environment.modules:
            if other is self:
                continue
            ox, oy = other.position
            # Check for overlap
            if (abs(x - ox) < (self.width + other.width) / 2) and (abs(y - oy) < (self.height + other.height) / 2):
                # Compute direction to move away
                dx = x - ox
                dy = y - oy
                # If dx or dy is zero, pick a random direction to avoid sticking
                if dx == 0 and dy == 0:
                    dx = random.choice([-1, 1])
                    dy = random.choice([-1, 1])
                elif dx == 0:
                    dx = random.choice([-1, 1])
                elif dy == 0:
                    dy = random.choice([-1, 1])
                # Normalize direction to unit step
                step_x = int(round(dx / abs(dx))) if dx != 0 else 0
                step_y = int(round(dy / abs(dy))) if dy != 0 else 0
                # Move by 1 unit in each direction away from the overlap
                x += step_x
                y += step_y
                moved = True
        if moved:
            self.position = (int(round(x)), int(round(y)))
            print(f"Module {self.module_id} moved to reduce overlap: {self.position}")
        return moved

class Environment:
    def __init__(self, bounds):
        """
        Initialize the environment.
        
        Parameters:
          bounds: A tuple (min_x, min_y, max_x, max_y) defining the design area.
        """
        self.bounds = bounds
        self.modules = []

    def add_module(self, module):
        self.modules.append(module)

    def update(self):
        """
        Update global environment conditions if needed.
        Currently a placeholder.
        """
        pass

    def check_global_constraints(self):
        """
        Placeholder for global constraint or collision checks among modules.
        """
        pass

    def shrink_bounds(self, shrink_amount=1):
        """
        Shrink the environment bounds by shrink_amount on all sides.
        """
        min_x, min_y, max_x, max_y = self.bounds
        # Prevent inversion of bounds
        if (max_x - min_x > 2 * shrink_amount) and (max_y - min_y > 2 * shrink_amount):
            min_x += shrink_amount
            min_y += shrink_amount
            max_x -= shrink_amount
            max_y -= shrink_amount
            self.bounds = (min_x, min_y, max_x, max_y)
            print(f"Environment bounds shrunk to: {self.bounds}")

    def plot_state(self, ax):
        """
        Plot the current state of the environment and its modules.
        Draws the environment boundary and each module as a rectangle.
        """
        ax.clear()
        min_x, min_y, max_x, max_y = self.bounds

        # Draw the environment bounds.
        env_rect = plt.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y,
                                 fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(env_rect)

        # Draw each module.
        for module in self.modules:
            x, y = module.position
            # Compute the bottom-left corner for the rectangle.
            bl_corner = (x - module.width / 2, y - module.height / 2)
            mod_rect = plt.Rectangle(bl_corner, module.width, module.height,
                                     color='red', alpha=0.6)
            ax.add_patch(mod_rect)
            # Optionally, add annotations.
            ax.annotate(str(module.module_id), (x, y), color='black', weight='bold',
                        fontsize=10, ha="center", va="center")
        
        # Always use the initial bounds for axis limits to keep scaling fixed
        ax.set_xlim(0 - 20, 100 + 20)
        ax.set_ylim(0 - 20, 100 + 20)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    def plot_overlap_bars(self, ax):
        """
        Plot a live bar chart showing the normalized overlap area (0..1) for each module.
        """
        ax.clear()
        overlaps = []
        labels = []
        for i, module in enumerate(self.modules):
            overlap_area = 0
            x1, y1 = module.position
            w1, h1 = module.width, module.height
            area1 = w1 * h1
            for j, other in enumerate(self.modules):
                if module is other:
                    continue
                x2, y2 = other.position
                w2, h2 = other.width, other.height
                # Calculate overlap in x and y
                dx = min(x1 + w1/2, x2 + w2/2) - max(x1 - w1/2, x2 - w2/2)
                dy = min(y1 + h1/2, y2 + h2/2) - max(y1 - h1/2, y2 - h2/2)
                if dx > 0 and dy > 0:
                    overlap_area += dx * dy
            # Normalize by module's own area, clamp to [0, 1]
            normalized_overlap = min(overlap_area / area1, 1.0) if area1 > 0 else 0
            overlaps.append(normalized_overlap)
            labels.append(str(module.module_id))
        ax.bar(labels, overlaps, color='orange')
        ax.set_ylabel("Normalized Overlap (0..1)")
        ax.set_xlabel("Module ID")
        ax.set_title("Normalized Overlap per Module")
        ax.set_ylim(0, 1)

class SimulationEngine:
    def __init__(self, environment):
        self.environment = environment

    def run(self, steps=10, plot=False, pause_time=0.5, plot_overlap=False):
        """
        Run the simulation for a specified number of steps.

        Parameters:
          steps: Number of simulation iterations.
          plot: If True, update and display an interactive plot at each step.
          pause_time: Delay in seconds between simulation steps in plotting mode.
          plot_overlap: If True, show a live bar chart of overlap per module.
        """
        if plot and plot_overlap:
            plt.ion()
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        elif plot:
            plt.ion()
            fig, ax1 = plt.subplots(figsize=(6, 6))
            ax2 = None
        else:
            ax1 = ax2 = None

        prev_positions = None
        unchanged_count = 0

        for step in range(steps):
            print(f"\n--- Step {step + 1} ---")
            # Store current positions before update
            current_positions = tuple((module.module_id, module.position) for module in self.environment.modules)

            # First, resolve overlaps
            overlap_resolved = False
            for module in self.environment.modules:
                if module.check_overlap_and_resolve(self.environment):
                    overlap_resolved = True

            # Center each module in its free space.
            for module in self.environment.modules:
                module.center_in_free_space(self.environment)
            self.environment.update()

            # Check if positions are unchanged from previous round
            new_positions = tuple((module.module_id, module.position) for module in self.environment.modules)
            if prev_positions is not None and new_positions == prev_positions:
                unchanged_count += 1
            else:
                unchanged_count = 0
            prev_positions = new_positions

            # Only shrink bounds if positions unchanged for two consecutive rounds
            if unchanged_count >= 2:
                self.environment.shrink_bounds(shrink_amount=1)
                unchanged_count = 0  # Reset after shrinking

            if plot:
                self.environment.plot_state(ax1)
                ax1.set_title(f"SWARM Simulation - Step {step + 1}")
                if plot_overlap and ax2 is not None:
                    self.environment.plot_overlap_bars(ax2)
                    ax2.set_title(f"Overlap per Module - Step {step + 1}")
                fig.canvas.draw_idle()
                plt.pause(pause_time)

        if plot:
            plt.ioff()
            plt.show()

# Example usage:
if __name__ == "__main__":
    # Define the environment bounds as (min_x, min_y, max_x, max_y).
    env = Environment(bounds=(0, 0, 100, 100))
    
    # Create a few modules with specified width and height.
    for i in range(5):
        # Place modules in a random location with some margin from the edge.
        pos = (random.randint(20, 80), random.randint(20, 80))
        # Ensure integer positions (already done by randint, but for clarity)
        module = ResponsiveModule(module_id=i, position=(int(pos[0]), int(pos[1])), width=random.randint(5, 20), height=random.randint(5, 20))
        env.add_module(module)
        
    engine = SimulationEngine(environment=env)
    engine.run(steps=100, plot=True, plot_overlap=True, pause_time=0.2)
