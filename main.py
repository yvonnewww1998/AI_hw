
import numpy as np
import turtle
import argparse
import time

# 從Maze.py 引入這些class跟functions
from maze import Maze, Particle, Robot, WeightedDistribution, weight_gaussian_kernel

def main(window_width, window_height, num_particles, sensor_limit_ratio, grid_height, grid_width, num_rows, num_cols, wall_prob, random_seed, robot_speed, kernel_sigma, particle_show_frequency):

    sensor_limit = sensor_limit_ratio * max(grid_height * num_rows, grid_width * num_cols) #設定sensor偵測範圍的上限( = sensor_limit_ratio傳感器的距離上限 * max(grid_height迷宮每個網格的高度 * num_rows迷宮的row數 , grid_width迷宮每個網格的寬度 * num_cols迷宮的column數))

    window = turtle.Screen() #利用turtle模組建立出一個初始的畫布，Screen是turtle下的一個Class，此行建立了一個此class的物件
    window.setup (width = window_width, height = window_height) # 設置主窗口的大小。

	# 建立出迷宮的形狀(設定 網格的寬/高度、行列數、牆出現的機率、for隨機的隨機種子)、調用Maze.py的函式
    world = Maze(grid_height = grid_height, grid_width = grid_width, num_rows = num_rows, num_cols = num_cols, wall_prob = wall_prob, random_seed = random_seed)

	#設定Robot-走迷宮的人 的 初始位置
    x = np.random.uniform(0, world.width)
    y = np.random.uniform(0, world.height)
    bob = Robot(x = x, y = y, maze = world, speed = robot_speed, sensor_limit = sensor_limit) #調用Maze.py的函式來處理

	#利用Particle幫Robot指引方向
    particles = list() #初始化一個list等要裝particles(每個particles的位置等等...)
    for i in range(num_particles): #在給定的 num_particles 之下產生出相應數量的particles(位置隨機)
        x = np.random.uniform(0, world.width)
        y = np.random.uniform(0, world.height)
        particles.append(Particle(x = x, y = y, maze = world, sensor_limit = sensor_limit)) #調用Maze.py的函式來處理、maze=剛剛用Maze建立出的迷宮形狀(word)

    time.sleep(1) #sleep(1)就是等一秒後, 如果被OS排班到我們才會繼續執行這個thread
    world.show_maze() #刷新迷宮畫面

    while True:

		#調用Maze.py的read_sensor函式來處理感測環境的部分
        readings_robot = bob.read_sensor(maze = world) #bob是上面初始給Robot的命名、

        particle_weight_total = 0 #初始total weight
        for particle in particles: #針對各個particle
            readings_particle = particle.read_sensor(maze = world)#調用Maze.py的read_sensor函式來處理感測環境的部分
            particle.weight = weight_gaussian_kernel(x1 = readings_robot, x2 = readings_particle, std = kernel_sigma)#調用Maze.py的weight_gaussian_kernel函式來計算particle's weight的部分
            particle_weight_total += particle.weight #加總算出particles total weight

        world.show_particles(particles = particles, show_frequency = particle_show_frequency) #顯示出particles(刷新畫面)
        world.show_robot(robot = bob) #顯示出robot(刷新畫面)
        world.show_estimated_location(particles = particles) #顯示出粒子的平均加總位置
        world.clear_objects() #刪掉所有戳記(all物品除了maze) -> move下一步時畫面就要做新的作圖了

        # Make sure normalization is not divided by zero 確保標準化的時候分母不是0(不能除)，這裡check完下一段就除了
        if particle_weight_total == 0:
            particle_weight_total = 1e-8sSS

        # Normalize particle weights 將 每個weight做標準化(除total)
        for particle in particles:
            particle.weight /= particle_weight_total

        # Resampling particles
        distribution = WeightedDistribution(particles = particles) # 實例化一個maze.py的class
        particles_new = list() # 初始化、功用：儲存Resample過後新的particles

        for i in range(num_particles): # resample次數不超過particles的總數量

            particle = distribution.random_select() # 利用WeightedDistributionclass裡面的random_select()來隨機選出一個particle

            if particle is None: # if選出來的particle是none的話(那個索引項<隨機數之前的索引項>)，就自己再生一個新的particle
                x = np.random.uniform(0, world.width) #np.random.uniform()：浮點、any value within the given interval is equally likely to be drawn by uniform.(抽到的機率均等)
                y = np.random.uniform(0, world.height) #np.random.uniform()：浮點、any value within the given interval is equally likely to be drawn by uniform.(抽到的機率均等)
                particles_new.append(Particle(x = x, y = y, maze = world, sensor_limit = sensor_limit)) #將新生出的Particle 加進剛剛存new particles的list中

            else: # 如果選出來的particle有值/不是none的話，就直接append上new particles的list中
                particles_new.append(Particle(x = particle.x, y = particle.y, maze = world, heading = particle.heading, sensor_limit = sensor_limit, noisy = True))

        particles = particles_new # 新的particles取代舊的(覆蓋)

        heading_old = bob.heading #resample前的heading方向
        bob.move(maze = world) # 調用Maze.py的函式move讓robot做出下一步的方向角度的決定
        heading_new = bob.heading #更新move完的heading方向
        dh = heading_new - heading_old #move前後的heading方位差

        for particle in particles: # 針對每個particle
            particle.heading = (particle.heading + dh) % 360 #*兩者相加算出heading的方向
            particle.try_move(maze = world, speed = bob.speed) # 調用Maze.py的函式算出particle的下一步移動方向


if __name__ == '__main__': #特此申明的原因：讓檔案在被引用時，不該執行的程式碼不被執行(因為有兩個.py檔，python直譯器會把相關引用的項目都一起執行)

    parser = argparse.ArgumentParser(description = 'Particle filter in maze.')

    window_width_default = 800 # 窗口寬度。
    window_height_default = 800 # 窗口高度。
    num_particles_default = 3000 # 粒子過濾器中使用的粒子數。
    sensor_limit_ratio_default = 0.3 #傳感器的距離上限（實際值：0-1 ）。0： 無用傳感器、1：完美的傳感器。
    grid_height_default = 100 # 迷宮中每個網格的高度。
    grid_width_default = 100 # 迷宮中每個網格的寬度。
    num_rows_default = 25 # 迷宮的row數
    num_cols_default = 25 # 迷宮的column數
    wall_prob_default = 0.25 # 牆出現的機率。
    random_seed_default = 100#用於隨機迷宮和粒子過濾器的隨機種子(算是能夠決定迷宮的形狀，有數字的話就是固定的迷宮形狀、None的話每次執行迷宮的樣子就都不一樣)。
    robot_speed_default = 10 # 機器人在迷宮中的移動速度。
    kernel_sigma_default = 500 # *高斯距離內核的Sigma。
    particle_show_frequency_default = 10 # 迷宮上顯示出顆粒的頻率。

    parser.add_argument('--window_width', type = int, help = 'Window width.', default = window_width_default)
    parser.add_argument('--window_height', type = int, help = 'Window height.', default = window_height_default)
    parser.add_argument('--num_particles', type = int, help = 'Number of particles used in particle filter.', default = num_particles_default)
    parser.add_argument('--sensor_limit_ratio', type = float, help = 'Distance limit of sensors (real value: 0 - 1). 0: Useless sensor; 1: Perfect sensor.', default = sensor_limit_ratio_default)
    parser.add_argument('--grid_height', type = int, help = 'Height for each grid of maze.', default = grid_height_default)
    parser.add_argument('--grid_width', type = int, help = 'Width for each grid of maze.', default = grid_width_default)
    parser.add_argument('--num_rows', type = int, help = 'Number of rows in maze', default = num_rows_default)
    parser.add_argument('--num_cols', type = int, help = 'Number of columns in maze', default = num_cols_default)
    parser.add_argument('--wall_prob', type = float, help = 'Wall probability of a random maze.', default = wall_prob_default)
    parser.add_argument('--random_seed', type = int, help = 'Random seed for random maze and particle filter.', default = random_seed_default)
    parser.add_argument('--robot_speed', type = int, help = 'Robot movement speed in maze.', default = robot_speed_default)
    parser.add_argument('--kernel_sigma', type = int, help = 'Standard deviation for Gaussian distance kernel.', default = kernel_sigma_default)
    parser.add_argument('--particle_show_frequency', type = int, help = 'Frequency of showing particles on maze.', default = particle_show_frequency_default)

    argv = parser.parse_args()

    window_width = argv.window_width
    window_height = argv.window_height
    num_particles = argv.num_particles
    sensor_limit_ratio = argv.sensor_limit_ratio
    grid_height = argv.grid_height
    grid_width = argv.grid_width
    num_rows = argv.num_rows
    num_cols = argv.num_cols
    wall_prob = argv.wall_prob
    random_seed = argv.random_seed
    robot_speed = argv.robot_speed
    kernel_sigma = argv.kernel_sigma
    particle_show_frequency = argv.particle_show_frequency

    main(window_width = window_width, window_height = window_height, num_particles = num_particles, sensor_limit_ratio = sensor_limit_ratio, grid_height = grid_height, grid_width = grid_width, num_rows = num_rows, num_cols = num_cols, wall_prob = wall_prob, random_seed = random_seed, robot_speed = robot_speed, kernel_sigma = kernel_sigma, particle_show_frequency = particle_show_frequency)
