import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
import math

# Health status constants
SUSCEPTIBLE = 0
EXPOSED = 1
INFECTED = 2
RECOVERED = 3
DEAD = 4
VACCINATED = 5
V_EXPOSED = 6  # Vaccinated and exposed
V_INFECTED = 7  # Vaccinated and infected

# Model parameters
P_EI = 0.1   # Probability of an exposed individual becoming infected
P_IR = 0.05  # Probability of an infected individual recovering
P_ID = 0.01  # Probability of an infected individual dying

infection_duration = 14

# Mutation effects
mutation_effect = {
    'P_EI': 0.3,   # After mutation, increased pathogenicity
    'P_ID': 0.005  # After mutation, decreased death rate
}

# Vaccine effects
vaccine_effect = {
    'P_EI': 0.5,   # Reduced infection rate after vaccination
    'P_ID': 0.1    # Reduced death rate after vaccination
}

# Create hexagonal grid
def create_hexagonal_grid(side_length):
    q, r = side_length, side_length
    grid = np.zeros((q, r))
    return grid

# Initialize node states
def initialize_node_states(grid):
    q, r = grid.shape
    for i in range(q):
        for j in range(r):
            grid[i, j] = SUSCEPTIBLE

# Seed initial infections
def seed_infections(grid, num_initial_infections):
    q, r = grid.shape
    initial_infections = np.random.choice(q * r, num_initial_infections, replace=False)
    for index in initial_infections:
        i, j = np.unravel_index(index, (q, r))
        grid[i, j] = EXPOSED

# Get contact neighbors for hexagonal grid (contact transmission)
def get_contact_neighbors(i, j, q, r):
    neighbors = []
    directions = [(+1, 0), (-1, 0), (0, +1), (0, -1), (+1, -1), (-1, +1)]
    for dir in directions:
        ni, nj = i + dir[0], j + dir[1]
        if 0 <= ni < q and 0 <= nj < r:
            neighbors.append((ni, nj))
    return neighbors

# Get aerosol neighbors within aerosol range for hexagonal grid
def get_aerosol_neighbors(i, j, q, r, aerosol_range):
    neighbors = []
    for ni in range(max(0, i - aerosol_range), min(q, i + aerosol_range + 1)):
        for nj in range(max(0, j - aerosol_range), min(r, j + aerosol_range + 1)):
            if (ni, nj) != (i, j):
                distance = math.sqrt((ni - i) ** 2 + (nj - j) ** 2)
                if distance <= aerosol_range:
                    neighbors.append((ni, nj, distance))
    return neighbors

# Vaccinate susceptible, exposed, and recovered individuals at a specific step
def vaccinate(grid):
    q, r = grid.shape
    for i in range(q):
        for j in range(r):
            if grid[i, j] not in {INFECTED, DEAD}:
                grid[i, j] = VACCINATED

def update_node_states(grid, droplet_range, aerosol_range):
    q, r = grid.shape
    new_grid = grid.copy()

    for i in range(q):
        for j in range(r):
            if grid[i, j] == SUSCEPTIBLE:
                # Contact transmission range
                contact_neighbors = get_contact_neighbors(i, j, q, r)
                for ni, nj in contact_neighbors:
                    if grid[ni, nj] == INFECTED and np.random.rand() < P_EI:
                        new_grid[i, j] = EXPOSED
                        break
                # Droplet transmission range
                droplet_neighbors = get_aerosol_neighbors(i, j, q, r, droplet_range)
                for ni, nj, distance in droplet_neighbors:
                    if grid[ni, nj] == INFECTED and np.random.rand() < P_EI * math.exp(-0.5 * distance):
                        new_grid[i, j] = EXPOSED
                        break
                # Aerosol transmission range
                aerosol_neighbors = get_aerosol_neighbors(i, j, q, r, aerosol_range)
                for ni, nj, distance in aerosol_neighbors:
                    if grid[ni, nj] == INFECTED and np.random.rand() < P_EI * math.exp(-0.1 * distance):
                        new_grid[i, j] = EXPOSED
                        break
            elif grid[i, j] == VACCINATED:
                # Do nothing, already vaccinated
                pass
            elif grid[i, j] == V_EXPOSED:
                # Do nothing, already vaccinated and exposed
                pass
            elif grid[i, j] == V_INFECTED:
                # Do nothing, already vaccinated and infected
                pass
            elif grid[i, j] == EXPOSED:
                if np.random.rand() < P_EI:
                    new_grid[i, j] = INFECTED
            elif grid[i, j] == INFECTED:
                if np.random.rand() < P_IR:
                    new_grid[i, j] = RECOVERED
                elif np.random.rand() < P_ID * (vaccine_effect['P_ID'] if grid[i, j] in {VACCINATED, V_EXPOSED} else 1):
                    new_grid[i, j] = DEAD

    return new_grid

# Check if the grid is in the desired stable state
def is_stable_state(grid):
    return np.all(np.isin(grid, [RECOVERED, DEAD, VACCINATED]))

# Plot dynamic spread of hexagonal grid (with droplet and aerosol transmission)
def plot_hexagonal_grid(grid, droplet_range, aerosol_range, vaccinate_step):
    q, r = grid.shape
    fig, ax = plt.subplots()
    cmap = mcolors.ListedColormap(['white', 'yellow', 'red', 'green', 'black', 'blue', 'orange', 'purple'])
    bounds = [0, 1, 2, 3, 4, 5, 6, 7]
    norm = mcolors.BoundaryNorm(bounds, cmap.N)

    img = ax.imshow(grid, cmap=cmap, norm=norm)

    def update(frame):
        nonlocal grid  # Ensure that we're modifying the outer grid variable
        if frame == vaccinate_step:
            vaccinate(grid)
        new_grid = update_node_states(grid, droplet_range, aerosol_range)
        if is_stable_state(new_grid):
            ani.event_source.stop()  # Stop animation if the grid has reached stable state
        grid[:] = new_grid  # Update the existing grid in place
        img.set_array(grid)
        return img,

    ani = animation.FuncAnimation(fig, update, frames=100, blit=True, interval=200)
    plt.title(f'Hexagonal Grid Model of COVID-19 Spread\n(Droplet Range: {droplet_range}, Aerosol Range: {aerosol_range})')
    plt.show()

# Calculate final death count and death rate at stable state
def calculate_final_stats_at_stable_state(grid, droplet_range, aerosol_range, vaccinate_step, max_iterations):
    current_grid = grid.copy()
    for step in range(max_iterations):
        if step == vaccinate_step:
            vaccinate(current_grid)
        new_grid = update_node_states(current_grid, droplet_range, aerosol_range)
        if is_stable_state(new_grid):
            break
        current_grid = new_grid

    total_nodes = current_grid.size
    dead_nodes = np.count_nonzero(current_grid == DEAD)
    death_rate = dead_nodes / total_nodes
    return dead_nodes, death_rate

# Execute animation
side_length = 30
grid = create_hexagonal_grid(side_length)

initialize_node_states(grid)
seed_infections(grid, num_initial_infections=5)

droplet_range = 2  # Droplet transmission range
aerosol_range = 4  # Aerosol transmission range
vaccinate_step = 15  # Vaccination step

plot_hexagonal_grid(grid, droplet_range, aerosol_range, vaccinate_step)

# Calculate and print final death count and death rate at stable state
max_iterations = 1000  # Maximum iterations to reach stable state
final_death_count, final_death_rate = calculate_final_stats_at_stable_state(grid, droplet_range, aerosol_range, vaccinate_step, max_iterations)
print(f"Final death count at stable state: {final_death_count}")
print(f"Final death rate at stable state: {final_death_rate:.2%}")
