import matplotlib.pyplot as plt

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
        action_options = ['move_right', 'move_left', 'move_up', 'move_down', 'rotate', 'center', None]
        action_to_idx = {a: i for i, a in enumerate(action_options)}
        module_ids = [m.module_id for m in self.environment.modules]
        action_history = {mid: [] for mid in module_ids}
        if plot and plot_action_history:
            if plot_overlap and plot_outside:
                plt.ion()
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
            step_actions = {}
            for module in self.environment.modules:
                action, value = module.choose_best_action(self.environment)
                step_actions[module.module_id] = action
                if module.perform_best_action(self.environment):
                    overlap_resolved = True
            for mid in module_ids:
                action_history[mid].append(step_actions.get(mid, None))
            self.environment.update()
            new_positions = tuple((module.module_id, module.position) for module in self.environment.modules)
            if prev_positions is not None and new_positions == prev_positions:
                unchanged_count += 1
            else:
                unchanged_count = 0
            prev_positions = new_positions
            if unchanged_count >= 2:
                self.environment.shrink_bounds(shrink_amount=1)
                unchanged_count = 0
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
                    ax_action.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=8)
                    ax_action.set_xlim(1, steps)
                    ax_action.set_ylim(-0.5, len(action_options) - 0.5)
                fig.canvas.draw_idle()
                plt.pause(pause_time)
        if plot:
            plt.ioff()
            plt.show()
