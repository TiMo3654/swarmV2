import matplotlib.pyplot as plt
import time

class SimulationEngine:
    def __init__(self, environment):
        self.environment = environment

    def run(self, steps=10, plot=False, pause_time=0.5, plot_overlap=False, plot_outside=False, plot_action_history=False, step_callback=None):
        """
        Run the simulation for a specified number of steps.

        Parameters:
          steps: Number of simulation iterations.
          plot: If True, update and display an interactive plot at each step.
          pause_time: Delay in seconds between simulation steps in plotting mode.
          plot_overlap: If True, show a live bar chart of overlap per module.
          plot_outside: If True, show a live bar chart of outside area per module.
          plot_action_history: If True, show a line plot of action history per module.
          step_callback: Optional function called at the end of each step with simulation state and stats.
        """
        action_options = ['move_right', 'move_left', 'move_up', 'move_down', 'rotate', 'center', 'evasion', None]
        action_to_idx = {a: i for i, a in enumerate(action_options)}
        module_ids = [m.module_id for m in self.environment.modules]
        action_history = {mid: [] for mid in module_ids}
        dead_space_history = []
        overlap_histories = {mid: [] for mid in module_ids}
        outside_histories = {mid: [] for mid in module_ids}

        if plot and plot_action_history:
            if plot_overlap and plot_outside:
                plt.ion()
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(18, 12))
                # Reduce upper row height by 30%: [2.1, 1, 1] and add vertical spacing
                gs = GridSpec(3, 3, height_ratios=[2.1, 1, 1], hspace=0.5)
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax3 = fig.add_subplot(gs[0, 2])
                ax_action = fig.add_subplot(gs[1, :])
                ax_deadspace = fig.add_subplot(gs[2, :])
            elif plot_overlap:
                plt.ion()
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(12, 12))
                gs = GridSpec(3, 2, height_ratios=[2.1, 1, 1], hspace=0.5)
                ax1 = fig.add_subplot(gs[0, 0])
                ax2 = fig.add_subplot(gs[0, 1])
                ax_action = fig.add_subplot(gs[1, :])
                ax_deadspace = fig.add_subplot(gs[2, :])
                ax3 = None
            else:
                plt.ion()
                from matplotlib.gridspec import GridSpec
                fig = plt.figure(figsize=(6, 12))
                gs = GridSpec(3, 1, height_ratios=[2.1, 1, 1], hspace=0.5)
                ax1 = fig.add_subplot(gs[0, 0])
                ax_action = fig.add_subplot(gs[1, 0])
                ax_deadspace = fig.add_subplot(gs[2, 0])
                ax2 = ax3 = None
        elif plot:
            if plot_overlap and plot_outside:
                plt.ion()
                fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
                ax_action = ax_deadspace = None
            elif plot_overlap:
                plt.ion()
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
                ax3 = None
                ax_action = ax_deadspace = None
            else:
                plt.ion()
                fig, ax1 = plt.subplots(figsize=(6, 6))
                ax2 = ax3 = ax_action = ax_deadspace = None
        else:
            ax1 = ax2 = ax3 = ax_action = ax_deadspace = None

        prev_positions = None

        for step in range(steps):
            step_actions = {}
            for module in self.environment.modules:
                action, value = module.choose_best_action(self.environment)
                step_actions[module.module_id] = action
                module.perform_best_action(self.environment)
            for mid in module_ids:
                action_history[mid].append(step_actions.get(mid, None))
            self.environment.update()
            # Dead space calculation
            min_x, min_y, max_x, max_y = self.environment.bounds
            boundary_area = (max_x - min_x) * (max_y - min_y)
            modules_area = sum(m.get_width_height()[0] * m.get_width_height()[1] for m in self.environment.modules)
            dead_space = boundary_area - modules_area
            dead_space_history.append(dead_space)
            # Overlap and outside area
            for module in self.environment.modules:
                w1, h1 = module.get_width_height()
                area1 = w1 * h1
                overlap_area = sum(module.overlap_area_with(other) for other in self.environment.modules if other is not module)
                normalized_overlap = min(overlap_area / area1, 1.0) if area1 > 0 else 0
                overlap_histories[module.module_id].append(normalized_overlap)
                outside_area = module.overlap_with_environment(self.environment)
                normalized_outside = min(outside_area / area1, 1.0) if area1 > 0 else 0
                outside_histories[module.module_id].append(normalized_outside)
            # Shrink bounds if all modules are overlap free and fully inside boundary
            all_ok = all(
                m.is_overlap_free(self.environment) and m.is_fully_inside_environment(self.environment)
                for m in self.environment.modules
            )
            if all_ok:
                self.environment.shrink_bounds(shrink_amount=1)
            # --- Callback for UI updates ---
            if step_callback is not None:
                step_callback({
                    'step': step,
                    'environment': self.environment,
                    'action_history': action_history,
                    'dead_space_history': dead_space_history,
                    'overlap_histories': overlap_histories,
                    'outside_histories': outside_histories,
                    'action_options': action_options,
                    'action_to_idx': action_to_idx,
                    'module_ids': module_ids
                })
                if pause_time > 0:
                    time.sleep(pause_time)
            elif plot:
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
                # --- Dead space plot ---
                if plot_action_history and ax_deadspace is not None:
                    ax_deadspace.clear()
                    ax_deadspace.plot(range(1, len(dead_space_history) + 1), dead_space_history, marker='o', color='green')
                    ax_deadspace.set_xlabel("Step")
                    ax_deadspace.set_ylabel("Dead Space")
                    ax_deadspace.set_title("Dead Space (Boundary Area - Modules Area)")
                    ax_deadspace.set_xlim(1, steps)
                    ax_deadspace.set_yscale('log')
                    ax_deadspace.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
                fig.canvas.draw_idle()
                plt.pause(pause_time)

        if plot:
            plt.ioff()
            plt.show()
