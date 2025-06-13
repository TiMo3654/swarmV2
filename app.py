import streamlit as st
import matplotlib.pyplot as plt
import random
from module import ResponsiveModule
from environment import Environment
from engine import SimulationEngine
import io
import plotly.graph_objs as go
import plotly.subplots as psub

st.set_page_config(page_title="Swarm Simulation", layout="wide")
st.title("Swarm Simulation with Dynamic Boundary")

# Sidebar controls
st.sidebar.header("Simulation Controls")
steps = st.sidebar.number_input("Number of Steps", min_value=1, max_value=1000, value=100)
pause_time = st.sidebar.number_input("Pause Time (s)", min_value=0.0, max_value=2.0, value=0.01, step=0.01)
num_modules = st.sidebar.number_input("Number of Modules", min_value=1, max_value=50, value=10)
random_seed = st.sidebar.number_input("Random Seed", min_value=0, max_value=10000, value=21)

# Start button
start_sim = st.button("Start Simulation")

if start_sim:
    random.seed(random_seed)
    env = Environment(bounds=(0, 0, 100, 100))
    for i in range(num_modules):
        pos = (random.randint(20, 80), random.randint(20, 80))
        module = ResponsiveModule(module_id=i, position=(int(pos[0]), int(pos[1])), width=random.randint(10, 20), height=random.randint(10, 20))
        env.add_module(module)
    engine = SimulationEngine(environment=env)

    plot_placeholder = st.empty()
    plot2_placeholder = st.empty()

    def streamlit_step_callback(state):
        step = state['step']
        env = state['environment']
        action_history = state['action_history']
        dead_space_history = state['dead_space_history']
        overlap_histories = state['overlap_histories']
        outside_histories = state['outside_histories']
        action_options = state['action_options']
        action_to_idx = state['action_to_idx']
        module_ids = state['module_ids']
        labels = [str(mid) for mid in module_ids]
        overlaps = [overlap_histories[mid][-1] for mid in module_ids]
        outsides = [outside_histories[mid][-1] for mid in module_ids]
        import plotly.graph_objs as go
        import plotly.subplots as psub
        min_x, min_y, max_x, max_y = 0, 0, 100, 100  # Fixed axis limits for state plot
        fig = psub.make_subplots(rows=1, cols=3, subplot_titles=(f"State at Step {step+1}", "Normalized Overlap per Module (Current)", "Normalized Area Outside Boundary (Current)"))
        # Draw the current (shrinking) boundary in blue
        min_x_env, min_y_env, max_x_env, max_y_env = env.bounds
        fig.add_shape(type="rect", x0=min_x_env, y0=min_y_env, x1=max_x_env, y1=max_y_env, line=dict(color="blue", width=3), row=1, col=1)
        # Draw the original fixed boundary in light gray for reference
        fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=100, line=dict(color="lightgray", width=2, dash="dash"), row=1, col=1)
        for module in env.modules:
            bl_x, bl_y, w, h = module.get_plot_rect()
            fig.add_shape(type="rect", x0=bl_x, y0=bl_y, x1=bl_x+w, y1=bl_y+h, fillcolor="red", opacity=0.6, line=dict(color="black", width=1), row=1, col=1)
            x, y = module.position
            fig.add_trace(go.Scatter(x=[x], y=[y], text=[f"{module.module_id}<br>{module.orientation}°"], mode="text", showlegend=False), row=1, col=1)
        # Set axis limits 20% larger than the initial boundary
        margin_x = (100 - 0) * 0.1
        margin_y = (100 - 0) * 0.1
        axis_min_x = 0 - margin_x
        axis_max_x = 100 + margin_x
        axis_min_y = 0 - margin_y
        axis_max_y = 100 + margin_y
        fig.update_xaxes(title_text="X", row=1, col=1, range=[axis_min_x, axis_max_x], dtick=20)
        fig.update_yaxes(title_text="Y", row=1, col=1, range=[axis_min_y, axis_max_y])
        fig.add_trace(go.Bar(x=labels, y=overlaps, marker_color='orange', name="Overlap"), row=1, col=2)
        fig.update_yaxes(title_text="Normalized Overlap (0..1)", row=1, col=2, range=[0,1])
        fig.update_xaxes(title_text="Module ID", row=1, col=2)
        fig.add_trace(go.Bar(x=labels, y=outsides, marker_color='blue', name="Outside"), row=1, col=3)
        fig.update_yaxes(title_text="Normalized Outside Area (0..1)", row=1, col=3, range=[0,1])
        fig.update_xaxes(title_text="Module ID", row=1, col=3)
        fig.update_layout(
            height=500,
            width=900,  # Set a constant width for the state plot
            autosize=False,  # Prevent Plotly from resizing
            showlegend=False,
        )
        plot_placeholder.plotly_chart(fig, use_container_width=False)  # Do not allow container to override width
        fig2 = psub.make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.15, subplot_titles=("Action per Module per Step", "Dead Space (Boundary Area - Modules Area)"))
        # Precompute the full x-axis for all steps
        x_full = list(range(1, steps + 1))
        for mid in module_ids:
            y = [action_to_idx[a] for a in action_history[mid]]
            # Pad y to length steps with None (or np.nan for better plotly handling)
            y_padded = y + [None] * (steps - len(y))
            fig2.add_trace(go.Scatter(x=x_full, y=y_padded, mode='lines+markers', name=f"Module {mid}"), row=1, col=1)
        fig2.update_yaxes(title_text="Action", tickvals=list(range(len(action_options))), ticktext=action_options, row=1, col=1, range=[-0.5, len(action_options)-0.5])
        fig2.update_xaxes(title_text="Step", row=1, col=1, range=[1, steps])
        fig2.update_layout(height=700, width=900)
        fig2.update_traces(showlegend=True, row=1, col=1)
        fig2.update_layout(legend=dict(yanchor="middle", y=0.5, xanchor="left", x=1.01, font=dict(size=10)))
        # Dead space plot, pad to steps
        y_deadspace = dead_space_history + [None] * (steps - len(dead_space_history))
        fig2.add_trace(go.Scatter(x=x_full, y=y_deadspace, mode='lines+markers', name="Dead Space", line=dict(color='green')), row=2, col=1)
        fig2.update_yaxes(title_text="Dead Space", type="log", row=2, col=1)
        fig2.update_xaxes(title_text="Step", row=2, col=1, range=[1, steps])
        fig2.update_traces(showlegend=False, row=2, col=1)
        plot2_placeholder.plotly_chart(fig2, use_container_width=True)

    engine.run(steps=steps, pause_time=pause_time, step_callback=streamlit_step_callback)
else:
    st.info("Press 'Start Simulation' to run the algorithm and display the plots.")
