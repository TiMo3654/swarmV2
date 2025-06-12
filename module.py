import math

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