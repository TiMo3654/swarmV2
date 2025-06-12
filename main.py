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
        self.orientation = 0  # 0 or 90 degrees, in degrees

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

    def get_corners(self):
        """
        Returns the corners of the rectangle as a list of (x, y) tuples, considering orientation.
        """
        x, y = self.position
        w, h = (self.width, self.height) if self.orientation % 180 == 0 else (self.height, self.width)
        half_w, half_h = w / 2, h / 2
        return [
            (x - half_w, y - half_h),
            (x + half_w, y - half_h),
            (x + half_w, y + half_h),
            (x - half_w, y + half_h)
        ]

    def get_bounds(self):
        """
        Returns (left, bottom, right, top) of the rectangle considering orientation.
        """
        corners = self.get_corners()
        xs = [c[0] for c in corners]
        ys = [c[1] for c in corners]
        return (min(xs), min(ys), max(xs), max(ys))

    def overlap_area_with(self, other):
        """
        Compute overlap area with another module, considering orientation.
        Only supports axis-aligned rectangles (0 or 90 deg).
        """
        left1, bottom1, right1, top1 = self.get_bounds()
        left2, bottom2, right2, top2 = other.get_bounds()
        dx = min(right1, right2) - max(left1, left2)
        dy = min(top1, top2) - max(bottom1, bottom2)
        if dx > 0 and dy > 0:
            return dx * dy
        return 0

    def overlap_with_environment(self, environment):
        """
        Returns the area of the module that extends beyond the environment boundary.
        """
        left, bottom, right, top = self.get_bounds()
        min_x, min_y, max_x, max_y = environment.bounds
        overlap = 0
        # Overlap on left
        if left < min_x:
            overlap += (min_x - left) * (top - bottom)
        # Overlap on right
        if right > max_x:
            overlap += (right - max_x) * (top - bottom)
        # Overlap on bottom
        if bottom < min_y:
            overlap += (right - left) * (min_y - bottom)
        # Overlap on top
        if top > max_y:
            overlap += (right - left) * (top - max_y)
        return overlap

    def choose_best_action(self, environment):
        """
        Decide whether to move (and in which direction), rotate (by 90 deg), or center in free space
        to reduce overlap or boundary extension.
        Returns a tuple (action, value), where action is one of:
        'move_right', 'move_left', 'move_up', 'move_down', 'rotate', 'center'
        """
        # Evaluate current overlap with modules and environment
        current_overlap = sum(self.overlap_area_with(other) for other in environment.modules if other is not self)
        current_boundary_overlap = self.overlap_with_environment(environment)

        # Try rotation
        self.orientation = (self.orientation + 90) % 180
        rotated_overlap = sum(self.overlap_area_with(other) for other in environment.modules if other is not self)
        rotated_boundary_overlap = self.overlap_with_environment(environment)
        self.orientation = (self.orientation + 90) % 180  # revert to original

        # If rotation reduces overlap or boundary extension, prefer rotation
        if (rotated_overlap < current_overlap) or (rotated_boundary_overlap < current_boundary_overlap):
            return ('rotate', 90)

        # Try centering in free space
        orig_pos = self.position
        left, bottom, right, top = self.evaluate_free_space(environment)
        center_x = (left + right) / 2
        center_y = (bottom + top) / 2
        self.position = (int(round(center_x)), int(round(center_y)))
        center_overlap = sum(self.overlap_area_with(other) for other in environment.modules if other is not self)
        center_boundary_overlap = self.overlap_with_environment(environment)
        self.position = orig_pos  # revert

        if (center_overlap < current_overlap) or (center_boundary_overlap < current_boundary_overlap):
            return ('center', (int(round(center_x)), int(round(center_y))))

        # Otherwise, try moving in each direction by 1 unit and pick the best
        best_action = None
        best_score = (current_overlap + current_boundary_overlap)
        directions = {
            'move_right': (1, 0),
            'move_left': (-1, 0),
            'move_up': (0, 1),
            'move_down': (0, -1)
        }
        for action, (dx, dy) in directions.items():
            self.position = (orig_pos[0] + dx, orig_pos[1] + dy)
            move_overlap = sum(self.overlap_area_with(other) for other in environment.modules if other is not self)
            move_boundary_overlap = self.overlap_with_environment(environment)
            score = move_overlap + move_boundary_overlap
            if score < best_score:
                best_score = score
                best_action = (action, 1)
            self.position = orig_pos  # revert

        if best_action:
            return best_action
        # No improvement found
        return (None, None)

    def perform_best_action(self, environment):
        """
        Perform the best action (move, rotate, or center) to reduce overlap or boundary extension.
        """
        action, value = self.choose_best_action(environment)
        if action == 'rotate':
            self.orientation = (self.orientation + 90) % 180
            print(f"Module {self.module_id} rotated to {self.orientation} degrees")
            return True
        elif action in ['move_right', 'move_left', 'move_up', 'move_down']:
            x, y = self.position
            if action == 'move_right':
                x += value
            elif action == 'move_left':
                x -= value
            elif action == 'move_up':
                y += value
            elif action == 'move_down':
                y -= value
            self.position = (int(round(x)), int(round(y)))
            print(f"Module {self.module_id} moved {action} to {self.position}")
            return True
        elif action == 'center':
            self.position = value
            print(f"Module {self.module_id} centered to position {self.position}")
            return True
        return False

    def get_width_height(self):
        """
        Returns (width, height) considering orientation.
        """
        if self.orientation % 180 == 0:
            return self.width, self.height
        else:
            return self.height, self.width

    def get_plot_rect(self):
        """
        Returns (bottom_left_x, bottom_left_y, width, height) for plotting, considering orientation.
        """
        x, y = self.position
        w, h = self.get_width_height()
        return (x - w / 2, y - h / 2, w, h)

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

        w, h = self.get_width_height()

        for other in environment.modules:
            if other is self:
                continue
            ox, oy = other.position
            ow, oh = other.get_width_height()
            o_left = ox - ow / 2
            o_right = ox + ow / 2
            o_bottom = oy - oh / 2
            o_top = oy + oh / 2

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

    def check_overlap_and_resolve(self, environment):
        """
        Try to resolve overlap or boundary extension by moving or rotating.
        Returns True if an action was performed.
        """
        return self.perform_best_action(environment)

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
            # Use orientation-aware plotting
            bl_x, bl_y, w, h = module.get_plot_rect()
            mod_rect = plt.Rectangle((bl_x, bl_y), w, h,
                                     color='red', alpha=0.6)
            ax.add_patch(mod_rect)
            # Optionally, add annotations.
            x, y = module.position
            ax.annotate(f"{module.module_id}\n{module.orientation}°", (x, y), color='black', weight='bold',
                        fontsize=10, ha="center", va="center")
        
        # Always use the initial bounds for axis limits to keep scaling fixed
        ax.set_xlim(0 - 20, 100 + 20)
        ax.set_ylim(0 - 20, 100 + 20)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

    def plot_overlap_bars(self, ax_overlap, ax_outside=None, show_outside=False):
        """
        Plot a live bar chart showing the normalized overlap area (0..1) for each module.
        If show_outside and ax_outside is given, also plot the normalized area outside the boundary.
        """
        ax_overlap.clear()
        overlaps = []
        labels = []
        outsides = []
        for module in self.modules:
            overlap_area = 0
            w1, h1 = module.get_width_height()
            area1 = w1 * h1
            for other in self.modules:
                if module is other:
                    continue
                overlap_area += module.overlap_area_with(other)
            normalized_overlap = min(overlap_area / area1, 1.0) if area1 > 0 else 0
            overlaps.append(normalized_overlap)
            labels.append(str(module.module_id))

            if show_outside and ax_outside is not None:
                outside_area = module.overlap_with_environment(self)
                normalized_outside = min(outside_area / area1, 1.0) if area1 > 0 else 0
                outsides.append(normalized_outside)

        ax_overlap.bar(labels, overlaps, color='orange')
        ax_overlap.set_ylabel("Normalized Overlap (0..1)")
        ax_overlap.set_xlabel("Module ID")
        ax_overlap.set_title("Normalized Overlap per Module")
        ax_overlap.set_ylim(0, 1)

        if show_outside and ax_outside is not None:
            ax_outside.clear()
            ax_outside.bar(labels, outsides, color='blue')
            ax_outside.set_ylabel("Normalized Outside Area (0..1)")
            ax_outside.set_xlabel("Module ID")
            ax_outside.set_title("Normalized Area Outside Boundary")
            ax_outside.set_ylim(0, 1)

class SimulationEngine:
    def __init__(self, environment):
        self.environment = environment

    def run(self, steps=10, plot=False, pause_time=0.5, plot_overlap=False, plot_outside=False, plot_action_history=False):
        """
        Run the simulation for a specified number of steps.

        Parameters:
          steps: Number of simulation iterations.
          plot: If True, update and display an interactive plot at each step.
          pause_time: Delay in seconds between simulation steps in plotting mode.
          plot_overlap: If True, show a live bar chart of overlap per module.
          plot_outside: If True, show a live bar chart of outside area per module.
          plot_action_history: If True, show a line plot of action history per module.
        """
        # --- Setup for action tracking and plotting ---
        action_options = ['move_right', 'move_left', 'move_up', 'move_down', 'rotate', 'center', None]
        action_to_idx = {a: i for i, a in enumerate(action_options)}
        module_ids = [m.module_id for m in self.environment.modules]
        action_history = {mid: [] for mid in module_ids}

        # --- Setup plotting ---
        if plot and plot_action_history:
            if plot_overlap and plot_outside:
                plt.ion()
                # 2 rows, 3 columns; bottom row: action history spans all columns
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(18, 10))
                gs = GridSpec(2, 3, height_ratios=[3, 1])
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax_action = fig.add_subplot(gs[1, :])
            elif plot_overlap:
                plt.ion()
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(12, 9))
                gs = GridSpec(2, 2, height_ratios=[3, 1])
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax_action = fig.add_subplot(gs[1, :])
                ax3 = None
            else:
                plt.ion()
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(6, 8))
                gs = GridSpec(2, 1, height_ratios=[3, 1])
                ax1 = fig.add_subplot(gs[0, 0])
                ax_action = fig.add_subplot(gs[1, 0])
                ax2 = ax3 = None
        elif plot:
            if plot_overlap and plot_outside:
                plt.ion()
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
            elif plot_overlap:
                plt.ion()
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
                ax3 = None
            else:
                plt.ion()
                fig, ax1 = plt.subplots(figsize=(6, 6))
                ax2 = ax3 = None
            ax_action = None
        else:
            ax1 = ax2 = ax3 = ax_action = None

        prev_positions = None
        unchanged_count = 0

        for step in range(steps):
            print(f"\n--- Step {step + 1} ---")
            # Store current positions before update
            current_positions = tuple((module.module_id, module.position) for module in self.environment.modules)

            # Only resolve overlaps, moving, rotating, or centering if it improves the situation
            overlap_resolved = False
            # --- Track actions for each module ---
            step_actions = {}
            for module in self.environment.modules:
                action, value = module.choose_best_action(self.environment)
                step_actions[module.module_id] = action
                if module.perform_best_action(self.environment):
                    overlap_resolved = True
            # Store actions in history
            for mid in module_ids:
                action_history[mid].append(step_actions.get(mid, None))

            # Remove centering in every round
            # for module in self.environment.modules:
            #     module.center_in_free_space(self.environment)
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
                    if plot_outside and ax3 is not None:
                        self.environment.plot_overlap_bars(ax2, ax3, show_outside=True)
                        ax2.set_title(f"Overlap per Module - Step {step + 1}")
                        ax3.set_title(f"Outside Area per Module - Step {step + 1}")
                    else:
                        self.environment.plot_overlap_bars(ax2, show_outside=False)
                        ax2.set_title(f"Overlap per Module - Step {step + 1}")

                # --- Plot action history as a line plot if enabled ---
                if plot_action_history and ax_action is not None:
                    ax_action.clear()
                    for mid in module_ids:
                        y = [action_to_idx[a] for a in action_history[mid]]
                        x = list(range(1, len(y) + 1))
                        ax_action.plot(x, y, marker='o', label=f"Module {mid}")
                    ax_action.set_yticks(list(range(len(action_options))))
                    ax_action.set_yticklabels(action_options)
                    ax_action.set_xlabel("Step")
                    ax_action.set_ylabel("Action")
                    ax_action.set_title("Action per Module per Step")
                    # Move legend outside the plot area (right side)
                    ax_action.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
                    ax_action.set_xlim(1, steps)
                    ax_action.set_ylim(-0.5, len(action_options) - 0.5)

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
    for i in range(8):
        # Place modules in a random location with some margin from the edge.
        pos = (random.randint(20, 80), random.randint(20, 80))
        # Ensure integer positions (already done by randint, but for clarity)
        module = ResponsiveModule(module_id=i, position=(int(pos[0]), int(pos[1])), width=random.randint(5, 20), height=random.randint(5, 20))
        env.add_module(module)
        
    engine = SimulationEngine(environment=env)
    engine.run(steps=100, plot=True, plot_overlap=True, plot_outside=True, plot_action_history=True, pause_time=0.2)
