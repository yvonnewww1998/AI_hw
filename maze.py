'''
Particle Filter in Maze

Lei Mao
University of Chicago

dukeleimao@gmail.com
'''

import numpy as np
import turtle
import bisect
import argparse

class Maze(object):

    def __init__(self, grid_height, grid_width, maze = None, num_rows = None, num_cols = None, wall_prob = None, random_seed = None):
        '''
        maze: 2D numpy array.
        passages are coded as a 4-bit number, with a bit value taking
        0 if there is a wall and 1 if there is no wall.
        The 1s register corresponds with a square's top edge,
        2s register the right edge,
        4s register the bottom edge,
        and 8s register the left edge.
        (numpy array)
        '''
		#�]�w��ӵe���j�p
        self.grid_height = grid_height
        self.grid_width = grid_width

		#��maze�إߤ@�ӫ��O
        if maze is not None:
            self.maze = maze
            self.num_rows = maze.shape[0]
            self.num_cols = maze.shape[1]
            self.fix_maze_boundary()
            self.fix_wall_inconsistency()
        else:
            assert num_rows is not None and num_cols is not None and
			is not None, 'Parameters for random maze should not be None.'
            self.random_maze(num_rows = num_rows, num_cols = num_cols, wall_prob = wall_prob, random_seed = random_seed)

        self.height = self.num_rows * self.grid_height
        self.width = self.num_cols * self.grid_width

        self.turtle_registration() #�I�s�U���禡

    def turtle_registration(self): # ���w�}�l�@�e���_�l��m(�Q�t���e�A��A���M�k�w�ˤF�|�ӶǷP���C)

        turtle.register_shape('tri', ((-3, -2), (0, 3), (3, -2), (0, 0)))

    def check_wall_inconsistency(self): #�T�{��O�_�����@�P���a��

        wall_errors = list()

        # Check vertical walls �ˬd������
        for i in range(self.num_rows):
            for j in range(self.num_cols-1): #j num_cols-1����]�O�̥k��cols���k��N�O�����䪺����F�A���ݭn�P�_�n���n����
				#�p�G�ۤv �� �U�@��/�ۤv�k�� �� �𭱤��@�P(ex.�ۤv����������A���k�䨺�컡�S�� -> erro)�A��̤��@�P�Nerro�A���N�N�����~�O���U��
                if (self.maze[i,j] & 2 != 0) != (self.maze[i,j+1] & 8 != 0): # 2�G�k��t�B8�G����t
                    wall_errors.append(((i,j), 'v')) #v�G�аO��vertical�����~
        # Check horizonal walls �ˬd������
        for i in range(self.num_rows-1): # i num_rows-1����]�O�̤U��rows���k��N�O�����䪺����F�A���ݭn�P�_�n���n����
            for j in range(self.num_cols):
				#�p�G�ۤv �� �U�@��/�ۤv�U�� �� �𭱤��@�P(ex.�ۤv����������A���U�����컡�S�� -> erro)�A��̤��@�P�Nerro�A���N�N�����~�O���U��
                if (self.maze[i,j] & 4 != 0) != (self.maze[i+1,j] & 1 != 0): # 4�G�U��t�B1�G�W��t
                    wall_errors.append(((i,j), 'h')) #h�G�аO��horizonal�����~�A��ɭԦ^�ǵ�fix_wall_inconsistency()�A���|�N���䳣����A�H��o�@�P��

        return wall_errors

    def fix_wall_inconsistency(self, verbose = True): #����A�C����������@�P���B�ɡA�����b���a��W����C
        '''
        Whenever there is a wall inconsistency, put a wall there.
        '''
        wall_errors = self.check_wall_inconsistency() #�ޥΤW����check_wall_inconsistency()�ӽT�{��O�_�����@�P���a��

        if wall_errors and verbose: #when��erros
            print('Warning: maze contains wall inconsistency.')

        for (i,j), error in wall_errors: #�w��S��erro�N�������S�w��쪺�� in check_wall_inconsistency()
            if error == 'v': #if erro ��verticle�G�N�⭱������(j��2-�k��Bj+1��8-����)�A�H��o�@�P��
                self.maze[i,j] |= 2
                self.maze[i,j+1] |= 8
            elif error == 'h': #if erro ��horizonal�G�N�⭱������(i��4-�U���Bi+1��1-�W��)�A�H��o�@�P��
                self.maze[i,j] |= 4
                self.maze[i+1,j] |= 1
            else: #�����O�W�zerro���ܫh�^��Exception�i����o����erro
                raise Exception('Unknown type of wall inconsistency.')
        return

    def fix_maze_boundary(self): #�T�wmaze�O���ɪ�
        '''
        Make sure that the maze is bounded.
        '''
		#��|���1/���_��(bitwise)
        for i in range(self.num_rows):
            self.maze[i,0] |= 8
            self.maze[i,-1] |= 2
        for j in range(self.num_cols):
            self.maze[0,j] |= 1
            self.maze[-1,j] |= 4

    def random_maze(self, num_rows, num_cols, wall_prob, random_seed = None): #����fun

        if random_seed is not None:
			# �Ω��H���g�c�M�ɤl�L�o�����H���ؤl(��O����M�w�g�c���Ϊ��A���Ʀr���ܴN�O�T�w���g�c�Ϊ��BNone���ܨC������g�c���ˤl�N�����@��)�C
            np.random.seed(random_seed)
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.maze = np.zeros((num_rows, num_cols), dtype = np.int8) #�]�wmaze�j�p

		#�إ�2:�k��t����Aj num_cols-1����]�O�̥k��cols���k��N�O�����䪺����F�A���ݭn�P�_�n���n����
        for i in range(self.num_rows):
            for j in range(self.num_cols-1):
				#rand()�X���Ʀr�O�_�p��wall_prob-��X�{�����v(�����Ʀr�V�p�Arand()�X�ӶV���e���p��A�X�{�𪺶V�p~wall_prob��1���ޫ��rand()���׳���wall_prob�p�A��˳�����)
                if np.random.rand() < wall_prob: #rand()�G�H���˥����[0, 1)
                    self.maze[i,j] |= 2 # |=�G²�g(is the bitwise-OR operation.)�B2�G�O���k��t�O�_����(����=1)
					# �Nself.maze[i,j] = self.maze[i,j] OR 2�G(self.maze[i,j]��ex.0000"1"0)���@��bit�n�O1���N�O�F< 01|00 = 01 >

		#�إ�4:�U��t����Ai num_rows-1����]�O�̤U��rows���k��N�O�����䪺����F�A���ݭn�P�_�n���n����
        for i in range(self.num_rows-1):
            for j in range(self.num_cols):
                if np.random.rand() < wall_prob:
                    self.maze[i,j] |= 4 # |=�G²�g(is the bitwise-OR operation.)�B4�G�O���U��t�O�_����(����=1)
					# �Nself.maze[i,j] = self.maze[i,j] OR 4�G(self.maze[i,j]��ex.000"1"00)���@��bit�n�O1���N�O�F< 01|00 = 01 >

        self.fix_maze_boundary() #�T�Omaze�O���ɪ�(�A�w�q�@���|�j�����ɪ��ȥH�T�O )
        self.fix_wall_inconsistency(verbose = False) #�T�O��S�����@�P���a��Acheck&������ܵL���~ verbose = False

    def permissibilities(self, cell): #�ˬd���w�椸�檺��V�O�_�O�Q���\���C(ex.���L�W�X�d������..)
        '''
        Check if the directions of a given cell are permissible.
        Return:
        (up, right, down, left)
        '''
        cell_value = self.maze[cell[0], cell[1]] #��l��cell_value
        return (cell_value & 1 == 0, cell_value & 2 == 0, cell_value & 4 == 0, cell_value & 8 == 0) #���n�q�L(�S���W�X�d��cell)�~�|�Otrue

    def distance_to_walls(self, coordinates): #for read_sensor()�ޥΡA���q�P�|�P������Z��
        '''
        Measure the distance of coordinates to nearest walls at four directions.
        Return:
        (up, right, down, left)
        '''

        x, y = coordinates

		# // -> ��
        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d1 = y - y // self.grid_height * self.grid_height
        while self.permissibilities(cell = (i,j))[0]: #���q���I�P�W��������Z���G[0]-The 1s register corresponds with a square's top edge
            i -= 1
            d1 += self.grid_height

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d2 = self.grid_width - (x - x // self.grid_width * self.grid_width)
        while self.permissibilities(cell = (i,j))[1]: #���q���I�P�k��������Z���G[1]10 2 -2s register the right edge
            j += 1
            d2 += self.grid_width

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d3 = self.grid_height - (y - y // self.grid_height * self.grid_height)
        while self.permissibilities(cell = (i,j))[2]: #���q���I�P�U��������Z���G[2]100 4-4s register the bottom edge
            i += 1
            d3 += self.grid_height

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d4 = x - x // self.grid_width * self.grid_width
        while self.permissibilities(cell = (i,j))[3]: #���q���I�P����������Z���G[3]1000 8-8s register the left edge
            j -= 1
            d4 += self.grid_width

        return [d1, d2, d3, d4] #�^�ǭp��n�P�|�誺�Z��

    def show_maze(self): #��ܥXmaze

		#�]�w�o�ӵe�������@�ɮy��
        turtle.setworldcoordinates(0, 0, self.width * 1.005, self.height * 1.005) #setworldcoordinates()�Gturtle�����禡(for����)

        wally = turtle.Turtle() #��l�Ƥ@��turtle����class
        wally.speed(0) #�]�w�e�����ʪ��t�סC�t�׵��ŬO1��10��������ơA�Ʀr�U�j�A�e�����ʷU�֡C
        wally.width(1.5) #�]�w�u���e��
        wally.hideturtle() #���õe������m�A��hide���ܷ|�X�{�@�ӽb�Y�N��e������m
        turtle.tracer(0, 0) #dummy method - to be overwritten by child class -> *�мg�� �]�S��L�a��ϥΨ�o�ӡC

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                permissibilities = self.permissibilities(cell = (i,j)) #permissibilities()�G�ϥΨ�W���۩R�����
                turtle.up() #Pull the pen up �V no drawing when moving.
                wally.setposition((j * self.grid_width, i * self.grid_height)) #�]�w�e������m
                # Set turtle heading orientation �]�w�e�����e�i��V
                # 0 - east, 90 - north, 180 - west, 270 - south

				# set�e�i��V��east
                wally.setheading(0)
                if not permissibilities[0]: #�p�Gcell direction�S�����ۮe
                    wally.down() #�}�l�e�X��wall
                else:
                    wally.up() #Pull the pen up �V no drawing when moving. ���ۮe�h���e
                wally.forward(self.grid_width) #�̷Ӻ���e�צA�h�e�i�@��

				# set�e�i��V��north
                wally.setheading(90)
                wally.up()
                if not permissibilities[1]: #�p�Gcell direction�S�����ۮe
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_height)

				 # set�e�i��V��west
                wally.setheading(180)
                wally.up()
                if not permissibilities[2]: #�p�Gcell direction�S�����ۮe
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_width)

				# set�e�i��V��south
                wally.setheading(270)
                wally.up()
                if not permissibilities[3]: #�p�Gcell direction�S�����ۮe
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_height)
                wally.up()

        turtle.update() #Perform a TurtleScreen update. To be used when tracer is turned off. �e����s(��ܥX�s�e�n���e��)


    def weight_to_color(self, weight): #�̷�particles��weight�h�վ���ܪ�color

        return '#%02x00%02x' % (int(weight * 255), int((1 - weight) * 255)) #weight �V���C��V�`


    def show_particles(self, particles, show_frequency = 10): #��ܥXparticles

        turtle.shape('tri') #�b�e���W�H'�T����'���

		#�w��C��particle�G
        for i, particle in enumerate(particles): #enumerate()�G�N�@�ӥi�M�����ƾڹ�H(�p�C��B���թΦr�Ŧ�)�զX���@�ӯ��ާǦC�A�P�ɦC�X�ƾکM�ƾڤU�СA�@��Φb for �`�����C
            if i % show_frequency == 0: #��ɶ���n��C10(�n��s�@����)
                turtle.setposition((particle.x, particle.y)) #�]�w�e������m
                turtle.setheading(90 - particle.heading) #�N�e������V�]�m��90 - particle.heading�C
                turtle.color(self.weight_to_color(particle.weight)) #�եΤW���۩R���禡weight_to_color()�G�̷�particles��weight�h�վ���ܪ�color
                turtle.stamp() #�b��e�Q�t��m�A�N�Q�t�Ϊ����ƥ��аO�b�e���W�C

        turtle.update() #Perform a TurtleScreen update. To be used when tracer is turned off. �e����s(��ܥX�s�e�n���e��)

    def show_estimated_location(self, particles):
        '''
        Show average weighted mean location of the particles. ��ܲɤl�����[�v��������m�C
        '''

		#��l�ƦU�Ѽ�
        x_accum = 0 #x���֭p
        y_accum = 0 #y���֭p
        heading_accum = 0 #heading���֭p
        weight_accum = 0 #weight���֭p

        num_particles = len(particles) #particles���`��(size)

        for particle in particles: #�w��C��particle�A�N�C�ӰѼƬۥ[���֭p

            weight_accum += particle.weight
            x_accum += particle.x * particle.weight
            y_accum += particle.y * particle.weight
            heading_accum += particle.heading * particle.weight

        if weight_accum == 0: #�X�{���~�A�N�|���Xmain.py��while True:�j��

            return False

		#��C�ӰѼƨ�����
        x_estimate = x_accum / weight_accum
        y_estimate = y_accum / weight_accum
        heading_estimate = heading_accum / weight_accum

		#��ܥX�ɤl�������[�`��m
        turtle.color('orange') #���O��⪺
        turtle.setposition(x_estimate, y_estimate)
        turtle.setheading(90 - heading_estimate) #�N�e������V�]�m��90 - particle.heading�C
        turtle.shape('turtle') #�b�e���W�H'�Q�t'���
        turtle.stamp() #�b��e�Q�t��m�A�N�Q�t�Ϊ����ƥ��аO�b�e���W�C
        turtle.update() #��s�e��

    def show_robot(self, robot):

        turtle.color('green') #���O��⪺
        turtle.shape('turtle') #�b�e���W�H'�Q�t'���
        turtle.shapesize(0.7, 0.7) #�]�w����ܪ������j�p
        turtle.setposition((robot.x, robot.y))
        turtle.setheading(90 - robot.heading) #�N�e������V�]�m��90 - particle.heading�C
        turtle.stamp() #�b��e�Q�t��m�A�N�Q�t�Ϊ����ƥ��аO�b�e���W�C
        turtle.update() #��s�e��

    def clear_objects(self):
        turtle.clearstamps() #�R���Ҧ��W�O(all���~���Fmaze)


class Particle(object):

    def __init__(self, x, y, maze, heading = None, weight = 1.0, sensor_limit = None, noisy = False):

        if heading is None: #��particle�@���H����heading��V
            heading = np.random.uniform(0,360)

        self.x = x
        self.y = y
        self.heading = heading
        self.weight = weight #���C��particle���Wweight(resampling�|�Ψ�)
        self.maze = maze
        self.sensor_limit = sensor_limit #�ǷP�����Z���W��

        if noisy: # When noisy = true
            std = max(self.maze.grid_height, self.maze.grid_width) * 0.2 # �]�w noist�i�b���W�U��

			#add_noise()�G�������~�t���y��
            self.x = self.add_noise(x = self.x, std = std)
            self.y = self.add_noise(x = self.y, std = std)
            self.heading = self.add_noise(x = self.heading, std = 360 * 0.05) #����heading����m(x)���V

        self.fix_invalid_particles() #�״_�L�Ĳɤl


    def fix_invalid_particles(self):

        # Fix invalid particles
        if self.x < 0: #��X�t���L��
            self.x = 0
        if self.x > self.maze.width:  #��X�p��maze�e�ת��L��
            self.x = self.maze.width * 0.9999
        if self.y < 0:
            self.y = 0
        if self.y > self.maze.height:  #��X�p��maze���ת��L��
            self.y = self.maze.height * 0.9999
        '''
        if self.heading > 360:
            self.heading -= 360
        if self.heading < 0:
            self.heading += 360
        '''
        self.heading = self.heading % 360 #�o�˴N�@�w���|�W�L360

    @property
    def state(self): #�^�Ƿ�e���A

        return (self.x, self.y, self.heading)

    def add_noise(self, x, std): #�^�ǥ[�nnoise����m

        return x + np.random.normal(0, std) #�����@�I�~�t��x

    def read_sensor(self, maze): #�P������(�Q�t���e�A��A���M�k�w�ˤF�|�ӶǷP���C)

        readings = maze.distance_to_walls(coordinates = (self.x, self.y)) #�ǷP���b�|�P(�W�U���k)���q�P�̪���������Z��

        heading = self.heading % 360 #�T�Oheading���פ��W�L360

        # Remove the compass from particle *�q�ɤl�W���U���n�w(������headings�ƭ����V -> �b�W�誺90�װ�����@����=�k�観�@����)
        if heading >= 45 and heading < 135: #���W�X��e���׽d��
            readings = readings
        elif heading >= 135 and heading < 225: #�ݭn����@��
            readings = readings[-1:] + readings[:-1]
            #readings = [readings[3], readings[0], readings[1], readings[2]] -> ���s�Ƨ�(:-1���̫�@�Ө����� -1�˼ƲĤ@�Ӫ��N��)
        elif heading >= 225 and heading < 315: #�ݭn������
            readings = readings[-2:] + readings[:-2]
            #readings = [readings[2], readings[3], readings[0], readings[1]] -> ���s�Ƨ�
        else: #�ݭn����T��
            readings = readings[-3:] + readings[:-3]
            #readings = [readings[1], readings[2], readings[3], readings[0]] -> ���s�Ƨ�

        if self.sensor_limit is not None: #if������P���Z���W��
            for i in range(len(readings)): #�w��C��readings
                if readings[i] > self.sensor_limit: #�����Z�����j�󵹩w�W�����A�Z�����]���W�����ƭ�
                    readings[i] = self.sensor_limit

        return readings #��^��o���P���ƾ�

    def try_move(self, speed, maze, noisy = False): # move�̷|�ϥΨ쪺�禡

		#���wheading��V��heading���סBradians����
        heading = self.heading
        heading_rad = np.radians(heading) #�����੷��

		 #��V���W���ʳt�״N�O�����n���ʪ��Z��
        dx = np.sin(heading_rad) * speed
        dy = np.cos(heading_rad) * speed

		#�U�@�B
        x = self.x + dx
        y = self.y + dy

		#���m//��l�e�� -> �����n�P�_�O�_�A��l�̬ƻ�
        gj1 = int(self.x // maze.grid_width)
        gi1 = int(self.y // maze.grid_height)
		#�s��m//��l�e�� -> �����n�P�_�O�_�A��l�̬ƻ�
        gj2 = int(x // maze.grid_width)
        gi2 = int(y // maze.grid_height)

        # Check if the particle is still in the maze �T�{���ʫ�ɤl�O�_�٦b�g�c��
        if gi2 < 0 or gi2 >= maze.num_rows or gj2 < 0 or gj2 >= maze.num_cols:
            return False

        # Move in the same grid #if�O�b�P���椤������(������)
        if gi1 == gi2 and gj1 == gj2:
            self.x = x
            self.y = y
            return True
        # Move across one grid vertically
        elif abs(gi1 - gi2) == 1 and abs(gj1 - gj2) == 0:#if�O�n���������ʨ줣�P����
            if maze.maze[min(gi1, gi2), gj1] & 4 != 0: #���䦳��N���ಾ
                return False
            else: #����S��~�i�H��
                self.x = x
                self.y = y
                return True
        # Move across one grid horizonally
        elif abs(gi1 - gi2) == 0 and abs(gj1 - gj2) == 1:#if�O�n���������ʨ줣�P����
            if maze.maze[gi1, min(gj1, gj2)] & 2 != 0:#���䦳��N���ಾ
                return False
            else: #����S��~�i�H��
                self.x = x
                self.y = y
                return True
        # Move across grids both vertically and horizonally
        elif abs(gi1 - gi2) == 1 and abs(gj1 - gj2) == 1: #if�O�n����+���������ʨ줣�P����

			#�p��n���ʪ������Z��
            x0 = max(gj1, gj2) * maze.grid_width
            y0 = (y - self.y) / (x - self.x) * (x0 - self.x) + self.y

            if maze.maze[int(y0 // maze.grid_height), min(gj1, gj2)] & 2 != 0:#���䦳��N���ಾ
                return False

			#�p��n���ʪ������Z��
            y0 = max(gi1, gi2) * maze.grid_height
            x0 = (x - self.x) / (y - self.y) * (y0 - self.y) + self.x

            if maze.maze[min(gi1, gi2), int(x0 // maze.grid_width)] & 4 != 0:#���䦳��N���ಾ
                return False

			 #����S��~�i�H��
            self.x = x
            self.y = y
            return True

        else:#�����O�W�z���p���ܴN�Oerro
            raise Exception('Unexpected collision detection.')


class Robot(Particle):

	#��l�ƾ����H
    def __init__(self, x, y, maze, heading = None, speed = 1.0, sensor_limit = None, noisy = True):

        super(Robot, self).__init__(x = x, y = y, maze = maze, heading = heading, sensor_limit = sensor_limit, noisy = noisy)
        self.step_count = 0
        self.noisy = noisy
        self.time_step = 0
        self.speed = speed

    def choose_random_direction(self): #�M�w��l���e����V(�H��)

        self.heading = np.random.uniform(0, 360) #np.random.uniform()�G�B�I�Bany value within the given interval is equally likely to be drawn by uniform.(��쪺���v����)

    def add_sensor_noise(self, x, z = 0.05): #��sensor�[�W�~�t�H�s�ynoise

        readings = list(x) # �Nsensing��T��J�@��list

        for i in range(len(readings)):
            std = readings[i] * z / 2 #�s�y�@��add noise���W��
            readings[i] = readings[i] + np.random.normal(0, std) #�Nreadings�[�Wnp.random.normal(0, std)�ӲV�c/�[�W�~�t

        return readings

    def read_sensor(self, maze):

        # Robot has error in reading the sensor while particles do not. �����H�bŪ���P����T�ɷ|���~�t�A���ɤl���|(*�w�])

		#���j�I�sread_sensor()
        readings = super(Robot, self).read_sensor(maze = maze) #super()�G�Ω�եΤ���(�W��)���@�Ӥ�k�A�O�ΨӸѨM�h���~�Ӱ��D��

        if self.noisy == True: #if init�]�w��true�G
            readings = self.add_sensor_noise(x = readings) #�Q��add_sensor_noise()�ӼW�[���T/�~�t

        return readings #�^�ǳB�z�n���B���~�t��readings(for Robot, particles���S��)

    def move(self, maze): #���骺����(�M�w�U�@�B)

        while True:
            self.time_step += 1 #�ɶ�++
            if self.try_move(speed = self.speed, maze = maze, noisy = False): #�I�s�W��禡try_move()
                break
            self.choose_random_direction()  #�M�w��l���e����V(�H��)


class WeightedDistribution(object): #Resampling �|�Ψ�

    def __init__(self, particles):

        accum = 0.0 #��l��accum�A�p��weight�`�M
        self.particles = particles #��l�ƪ���(�U���|��)
        self.distribution = list() #��l�ƪ���(�U���|��)
        for particle in self.particles: #���C��particle�]for�j��
            accum += particle.weight #�p��weight�`�M
            self.distribution.append(accum) #�Nweight�`�M���Jdistribution(add)

    def random_select(self): #Resampling �|�Ψ�

        try:
			# �^�Ǥ@�ӯS�w��particle(�bparticles[bisect_left()�^�Ǫ����J��m])�A�H�������
            return self.particles[bisect.bisect_left(self.distribution, np.random.uniform(0, 1))] #bisect_left()�G�}�C�G���t��k�A�^�Ǫ����J��m�|�b�Ҧ� self.distribution ���� np.random.uniform(0, 1)<�H���X����> ���e���]����^
																		#np.random.uniform()�G�B�I�Bany value within the given interval is equally likely to be drawn by uniform.(��쪺���v����)
        except IndexError: # ���~(�S��weight�����weight���v����Resample)#np.random.uniform()�G�B�I�Bany value within the given interval is equally likely to be drawn by uniform.(��쪺���v����)
            # When all particles have weights zero
            return None

def euclidean_distance(x1, x2): # �p��ڦ��Z�� ex.���Ia(x1,y1)�Pb(x2,y2)���ڦ��Z�� = [(x1-x2)^2+(y1-y2)^2]^1/2

    return np.linalg.norm(np.asarray(x1) - np.asarray(x2)) # �p��X��array�����I���зǶZ��

def weight_gaussian_kernel(x1, x2, std = 10):

    distance = euclidean_distance(x1 = x1, x2 = x2) # �p��ڦ��Z���G�O�bm���Ŷ�������I�������u��Z���C
    return np.exp(-distance ** 2 / (2 * std)) # �����ƺ�Xparticle's weight & ��^







