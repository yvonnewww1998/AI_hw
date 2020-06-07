
import numpy as np
import turtle
import argparse
import time

# �qMaze.py �ޤJ�o��class��functions
from maze import Maze, Particle, Robot, WeightedDistribution, weight_gaussian_kernel

def main(window_width, window_height, num_particles, sensor_limit_ratio, grid_height, grid_width, num_rows, num_cols, wall_prob, random_seed, robot_speed, kernel_sigma, particle_show_frequency):

    sensor_limit = sensor_limit_ratio * max(grid_height * num_rows, grid_width * num_cols) #�]�wsensor�����d�򪺤W��( = sensor_limit_ratio�ǷP�����Z���W�� * max(grid_height�g�c�C�Ӻ��檺���� * num_rows�g�c��row�� , grid_width�g�c�C�Ӻ��檺�e�� * num_cols�g�c��column��))

    window = turtle.Screen() #�Q��turtle�ҲիإߥX�@�Ӫ�l���e���AScreen�Oturtle�U���@��Class�A����إߤF�@�Ӧ�class������
    window.setup (width = window_width, height = window_height) # �]�m�D���f���j�p�C

	# �إߥX�g�c���Ϊ�(�]�w ���檺�e/���סB��C�ơB��X�{�����v�Bfor�H�����H���ؤl)�B�ե�Maze.py���禡
    world = Maze(grid_height = grid_height, grid_width = grid_width, num_rows = num_rows, num_cols = num_cols, wall_prob = wall_prob, random_seed = random_seed)

	#�]�wRobot-���g�c���H �� ��l��m
    x = np.random.uniform(0, world.width)
    y = np.random.uniform(0, world.height)
    bob = Robot(x = x, y = y, maze = world, speed = robot_speed, sensor_limit = sensor_limit) #�ե�Maze.py���禡�ӳB�z

	#�Q��Particle��Robot���ޤ�V
    particles = list() #��l�Ƥ@��list���n��particles(�C��particles����m����...)
    for i in range(num_particles): #�b���w�� num_particles ���U���ͥX�����ƶq��particles(��m�H��)
        x = np.random.uniform(0, world.width)
        y = np.random.uniform(0, world.height)
        particles.append(Particle(x = x, y = y, maze = world, sensor_limit = sensor_limit)) #�ե�Maze.py���禡�ӳB�z�Bmaze=����Maze�إߥX���g�c�Ϊ�(word)

    time.sleep(1) #sleep(1)�N�O���@���, �p�G�QOS�ƯZ��ڭ̤~�|�~�����o��thread
    world.show_maze() #��s�g�c�e��

    while True:

		#�ե�Maze.py��read_sensor�禡�ӳB�z�P�����Ҫ�����
        readings_robot = bob.read_sensor(maze = world) #bob�O�W����l��Robot���R�W�B

        particle_weight_total = 0 #��ltotal weight
        for particle in particles: #�w��U��particle
            readings_particle = particle.read_sensor(maze = world)#�ե�Maze.py��read_sensor�禡�ӳB�z�P�����Ҫ�����
            particle.weight = weight_gaussian_kernel(x1 = readings_robot, x2 = readings_particle, std = kernel_sigma)#�ե�Maze.py��weight_gaussian_kernel�禡�ӭp��particle's weight������
            particle_weight_total += particle.weight #�[�`��Xparticles total weight

        world.show_particles(particles = particles, show_frequency = particle_show_frequency) #��ܥXparticles(��s�e��)
        world.show_robot(robot = bob) #��ܥXrobot(��s�e��)
        world.show_estimated_location(particles = particles) #��ܥX�ɤl�������[�`��m
        world.clear_objects() #�R���Ҧ��W�O(all���~���Fmaze) -> move�U�@�B�ɵe���N�n���s���@�ϤF

        # Make sure normalization is not divided by zero �T�O�зǤƪ��ɭԤ������O0(���ణ)�A�o��check���U�@�q�N���F
        if particle_weight_total == 0:
            particle_weight_total = 1e-8sSS

        # Normalize particle weights �N �C��weight���зǤ�(��total)
        for particle in particles:
            particle.weight /= particle_weight_total

        # Resampling particles
        distribution = WeightedDistribution(particles = particles) # ��ҤƤ@��maze.py��class
        particles_new = list() # ��l�ơB�\�ΡG�x�sResample�L��s��particles

        for i in range(num_particles): # resample���Ƥ��W�Lparticles���`�ƶq

            particle = distribution.random_select() # �Q��WeightedDistributionclass�̭���random_select()���H����X�@��particle

            if particle is None: # if��X�Ӫ�particle�Onone����(���ӯ��޶�<�H���Ƥ��e�����޶�>)�A�N�ۤv�A�ͤ@�ӷs��particle
                x = np.random.uniform(0, world.width) #np.random.uniform()�G�B�I�Bany value within the given interval is equally likely to be drawn by uniform.(��쪺���v����)
                y = np.random.uniform(0, world.height) #np.random.uniform()�G�B�I�Bany value within the given interval is equally likely to be drawn by uniform.(��쪺���v����)
                particles_new.append(Particle(x = x, y = y, maze = world, sensor_limit = sensor_limit)) #�N�s�ͥX��Particle �[�i���snew particles��list��

            else: # �p�G��X�Ӫ�particle����/���Onone���ܡA�N����append�Wnew particles��list��
                particles_new.append(Particle(x = particle.x, y = particle.y, maze = world, heading = particle.heading, sensor_limit = sensor_limit, noisy = True))

        particles = particles_new # �s��particles���N�ª�(�л\)

        heading_old = bob.heading #resample�e��heading��V
        bob.move(maze = world) # �ե�Maze.py���禡move��robot���X�U�@�B����V���ת��M�w
        heading_new = bob.heading #��smove����heading��V
        dh = heading_new - heading_old #move�e�᪺heading���t

        for particle in particles: # �w��C��particle
            particle.heading = (particle.heading + dh) % 360 #*��̬ۥ[��Xheading����V
            particle.try_move(maze = world, speed = bob.speed) # �ե�Maze.py���禡��Xparticle���U�@�B���ʤ�V


if __name__ == '__main__': #�S���ө�����]�G���ɮצb�Q�ޥήɡA���Ӱ��檺�{���X���Q����(�]�������.py�ɡApython��Ķ���|������ޥΪ����س��@�_����)

    parser = argparse.ArgumentParser(description = 'Particle filter in maze.')

    window_width_default = 800 # ���f�e�סC
    window_height_default = 800 # ���f���סC
    num_particles_default = 3000 # �ɤl�L�o�����ϥΪ��ɤl�ơC
    sensor_limit_ratio_default = 0.3 #�ǷP�����Z���W���]��ڭȡG0-1 �^�C0�G �L�ζǷP���B1�G�������ǷP���C
    grid_height_default = 100 # �g�c���C�Ӻ��檺���סC
    grid_width_default = 100 # �g�c���C�Ӻ��檺�e�סC
    num_rows_default = 25 # �g�c��row��
    num_cols_default = 25 # �g�c��column��
    wall_prob_default = 0.25 # ��X�{�����v�C
    random_seed_default = 100#�Ω��H���g�c�M�ɤl�L�o�����H���ؤl(��O����M�w�g�c���Ϊ��A���Ʀr���ܴN�O�T�w���g�c�Ϊ��BNone���ܨC������g�c���ˤl�N�����@��)�C
    robot_speed_default = 10 # �����H�b�g�c�������ʳt�סC
    kernel_sigma_default = 500 # *�����Z�����֪�Sigma�C
    particle_show_frequency_default = 10 # �g�c�W��ܥX���ɪ��W�v�C

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
