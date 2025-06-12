import matplotlib.pyplot as plt

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
        env_rect = plt.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y,
                                 fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(env_rect)
        for module in self.modules:
            bl_x, bl_y, w, h = module.get_plot_rect()
            mod_rect = plt.Rectangle((bl_x, bl_y), w, h,
                                     color='red', alpha=0.6)
            ax.add_patch(mod_rect)
            x, y = module.position
            ax.annotate(f"{module.module_id}\n{module.orientation}°", (x, y), color='black', weight='bold',
                        fontsize=10, ha="center", va="center")
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
