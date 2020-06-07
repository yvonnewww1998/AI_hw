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
		#設定整個畫布大小
        self.grid_height = grid_height
        self.grid_width = grid_width

		#幫maze建立一個型別
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

        self.turtle_registration() #呼叫下面函式

    def turtle_registration(self): # 給定開始作畫的起始位置(烏龜的前，後，左和右安裝了四個傳感器。)

        turtle.register_shape('tri', ((-3, -2), (0, 3), (3, -2), (0, 0)))

    def check_wall_inconsistency(self): #確認牆是否有不一致的地方

        wall_errors = list()

        # Check vertical walls 檢查垂直牆
        for i in range(self.num_rows):
            for j in range(self.num_cols-1): #j num_cols-1的原因是最右的cols的右邊就是最邊邊的牆壁了，不需要判斷要不要給牆
				#如果自己 跟 下一個/自己右邊 的 牆面不一致(ex.自己說中間有牆，但右邊那位說沒有 -> erro)，兩者不一致就erro，那就將此錯誤記錄下來
                if (self.maze[i,j] & 2 != 0) != (self.maze[i,j+1] & 8 != 0): # 2：右邊緣、8：左邊緣
                    wall_errors.append(((i,j), 'v')) #v：標記為vertical的錯誤
        # Check horizonal walls 檢查水平牆
        for i in range(self.num_rows-1): # i num_rows-1的原因是最下的rows的右邊就是最邊邊的牆壁了，不需要判斷要不要給牆
            for j in range(self.num_cols):
				#如果自己 跟 下一個/自己下面 的 牆面不一致(ex.自己說中間有牆，但下面那位說沒有 -> erro)，兩者不一致就erro，那就將此錯誤記錄下來
                if (self.maze[i,j] & 4 != 0) != (self.maze[i+1,j] & 1 != 0): # 4：下邊緣、1：上邊緣
                    wall_errors.append(((i,j), 'h')) #h：標記為horizonal的錯誤，到時候回傳給fix_wall_inconsistency()，它會將兩邊都給牆，以獲得一致性

        return wall_errors

    def fix_wall_inconsistency(self, verbose = True): #填牆，每當牆壁有不一致之處時，都應在此地放上牆壁。
        '''
        Whenever there is a wall inconsistency, put a wall there.
        '''
        wall_errors = self.check_wall_inconsistency() #引用上面的check_wall_inconsistency()來確認牆是否有不一致的地方

        if wall_errors and verbose: #when有erros
            print('Warning: maze contains wall inconsistency.')

        for (i,j), error in wall_errors: #針對特並erro代號給予特定方位的牆 in check_wall_inconsistency()
            if error == 'v': #if erro 為verticle：將兩面都給牆(j的2-右邊、j+1的8-左邊)，以獲得一致性
                self.maze[i,j] |= 2
                self.maze[i,j+1] |= 8
            elif error == 'h': #if erro 為horizonal：將兩面都給牆(i的4-下面、i+1的1-上面)，以獲得一致性
                self.maze[i,j] |= 4
                self.maze[i+1,j] |= 1
            else: #都不是上述erro的話則回傳Exception告知獲得未知erro
                raise Exception('Unknown type of wall inconsistency.')
        return

    def fix_maze_boundary(self): #確定maze是有界的
        '''
        Make sure that the maze is bounded.
        '''
		#把四邊用1/牆填起來(bitwise)
        for i in range(self.num_rows):
            self.maze[i,0] |= 8
            self.maze[i,-1] |= 2
        for j in range(self.num_cols):
            self.maze[0,j] |= 1
            self.maze[-1,j] |= 4

    def random_maze(self, num_rows, num_cols, wall_prob, random_seed = None): #建牆的fun

        if random_seed is not None:
			# 用於隨機迷宮和粒子過濾器的隨機種子(算是能夠決定迷宮的形狀，有數字的話就是固定的迷宮形狀、None的話每次執行迷宮的樣子就都不一樣)。
            np.random.seed(random_seed)
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.maze = np.zeros((num_rows, num_cols), dtype = np.int8) #設定maze大小

		#建立2:右邊緣的牆，j num_cols-1的原因是最右的cols的右邊就是最邊邊的牆壁了，不需要判斷要不要給牆
        for i in range(self.num_rows):
            for j in range(self.num_cols-1):
				#rand()出的數字是否小於wall_prob-牆出現的機率(給的數字越小，rand()出來越不容易小於，出現牆的越小~wall_prob給1不管怎麼rand()答案都比wall_prob小，怎樣都有牆)
                if np.random.rand() < wall_prob: #rand()：隨機樣本位於[0, 1)
                    self.maze[i,j] |= 2 # |=：簡寫(is the bitwise-OR operation.)、2：記錄右邊緣是否有牆(有牆=1)
					# 將self.maze[i,j] = self.maze[i,j] OR 2：(self.maze[i,j]的ex.0000"1"0)那一個bit要是1的就是了< 01|00 = 01 >

		#建立4:下邊緣的牆，i num_rows-1的原因是最下的rows的右邊就是最邊邊的牆壁了，不需要判斷要不要給牆
        for i in range(self.num_rows-1):
            for j in range(self.num_cols):
                if np.random.rand() < wall_prob:
                    self.maze[i,j] |= 4 # |=：簡寫(is the bitwise-OR operation.)、4：記錄下邊緣是否有牆(有牆=1)
					# 將self.maze[i,j] = self.maze[i,j] OR 4：(self.maze[i,j]的ex.000"1"00)那一個bit要是1的就是了< 01|00 = 01 >

        self.fix_maze_boundary() #確保maze是有界的(再定義一次四大方位邊界的值以確保 )
        self.fix_wall_inconsistency(verbose = False) #確保牆沒有不一致的地方，check&填完牆後表示無錯誤 verbose = False

    def permissibilities(self, cell): #檢查給定單元格的方向是否是被允許的。(ex.有無超出範圍之類的..)
        '''
        Check if the directions of a given cell are permissible.
        Return:
        (up, right, down, left)
        '''
        cell_value = self.maze[cell[0], cell[1]] #初始化cell_value
        return (cell_value & 1 == 0, cell_value & 2 == 0, cell_value & 4 == 0, cell_value & 8 == 0) #都要通過(沒有超出範圍的cell)才會是true

    def distance_to_walls(self, coordinates): #for read_sensor()引用，測量與四周牆壁的距離
        '''
        Measure the distance of coordinates to nearest walls at four directions.
        Return:
        (up, right, down, left)
        '''

        x, y = coordinates

		# // -> 除
        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d1 = y - y // self.grid_height * self.grid_height
        while self.permissibilities(cell = (i,j))[0]: #測量此點與上方牆壁的距離：[0]-The 1s register corresponds with a square's top edge
            i -= 1
            d1 += self.grid_height

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d2 = self.grid_width - (x - x // self.grid_width * self.grid_width)
        while self.permissibilities(cell = (i,j))[1]: #測量此點與右方牆壁的距離：[1]10 2 -2s register the right edge
            j += 1
            d2 += self.grid_width

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d3 = self.grid_height - (y - y // self.grid_height * self.grid_height)
        while self.permissibilities(cell = (i,j))[2]: #測量此點與下方牆壁的距離：[2]100 4-4s register the bottom edge
            i += 1
            d3 += self.grid_height

        i = int(y // self.grid_height)
        j = int(x // self.grid_width)
        d4 = x - x // self.grid_width * self.grid_width
        while self.permissibilities(cell = (i,j))[3]: #測量此點與左方牆壁的距離：[3]1000 8-8s register the left edge
            j -= 1
            d4 += self.grid_width

        return [d1, d2, d3, d4] #回傳計算好與四方的距離

    def show_maze(self): #顯示出maze

		#設定這個畫布中的世界座標
        turtle.setworldcoordinates(0, 0, self.width * 1.005, self.height * 1.005) #setworldcoordinates()：turtle中的函式(for視窗)

        wally = turtle.Turtle() #初始化一個turtle中的class
        wally.speed(0) #設定畫筆移動的速度。速度等級是1到10之間的整數，數字愈大，畫筆移動愈快。
        wally.width(1.5) #設定線條寬度
        wally.hideturtle() #隱藏畫筆的位置，不hide的話會出現一個箭頭代表畫筆的位置
        turtle.tracer(0, 0) #dummy method - to be overwritten by child class -> *覆寫用 也沒其他地方使用到這個。

        for i in range(self.num_rows):
            for j in range(self.num_cols):
                permissibilities = self.permissibilities(cell = (i,j)) #permissibilities()：使用到上面自命的函數
                turtle.up() #Pull the pen up – no drawing when moving.
                wally.setposition((j * self.grid_width, i * self.grid_height)) #設定畫筆的位置
                # Set turtle heading orientation 設定畫筆的前進方向
                # 0 - east, 90 - north, 180 - west, 270 - south

				# set前進方向為east
                wally.setheading(0)
                if not permissibilities[0]: #如果cell direction沒有不相容
                    wally.down() #開始畫出此wall
                else:
                    wally.up() #Pull the pen up – no drawing when moving. 不相容則不畫
                wally.forward(self.grid_width) #依照網格寬度再去前進一格

				# set前進方向為north
                wally.setheading(90)
                wally.up()
                if not permissibilities[1]: #如果cell direction沒有不相容
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_height)

				 # set前進方向為west
                wally.setheading(180)
                wally.up()
                if not permissibilities[2]: #如果cell direction沒有不相容
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_width)

				# set前進方向為south
                wally.setheading(270)
                wally.up()
                if not permissibilities[3]: #如果cell direction沒有不相容
                    wally.down()
                else:
                    wally.up()
                wally.forward(self.grid_height)
                wally.up()

        turtle.update() #Perform a TurtleScreen update. To be used when tracer is turned off. 畫布更新(顯示出新畫好的畫面)


    def weight_to_color(self, weight): #依照particles的weight去調整顯示的color

        return '#%02x00%02x' % (int(weight * 255), int((1 - weight) * 255)) #weight 越重顏色越深


    def show_particles(self, particles, show_frequency = 10): #顯示出particles

        turtle.shape('tri') #在畫布上以'三角形'顯示

		#針對每個particle：
        for i, particle in enumerate(particles): #enumerate()：將一個可遍歷的數據對象(如列表、元組或字符串)組合為一個索引序列，同時列出數據和數據下標，一般用在 for 循環當中。
            if i % show_frequency == 0: #當時間剛好到每10(要更新一次時)
                turtle.setposition((particle.x, particle.y)) #設定畫筆的位置
                turtle.setheading(90 - particle.heading) #將畫筆的方向設置為90 - particle.heading。
                turtle.color(self.weight_to_color(particle.weight)) #調用上面自命的函式weight_to_color()：依照particles的weight去調整顯示的color
                turtle.stamp() #在當前烏龜位置，將烏龜形狀的副本標記在畫布上。

        turtle.update() #Perform a TurtleScreen update. To be used when tracer is turned off. 畫布更新(顯示出新畫好的畫面)

    def show_estimated_location(self, particles):
        '''
        Show average weighted mean location of the particles. 顯示粒子平均加權的平均位置。
        '''

		#初始化各參數
        x_accum = 0 #x的累計
        y_accum = 0 #y的累計
        heading_accum = 0 #heading的累計
        weight_accum = 0 #weight的累計

        num_particles = len(particles) #particles的總數(size)

        for particle in particles: #針對每個particle，將每個參數相加做累計

            weight_accum += particle.weight
            x_accum += particle.x * particle.weight
            y_accum += particle.y * particle.weight
            heading_accum += particle.heading * particle.weight

        if weight_accum == 0: #出現錯誤，將會跳出main.py的while True:迴圈

            return False

		#對每個參數取平均
        x_estimate = x_accum / weight_accum
        y_estimate = y_accum / weight_accum
        heading_estimate = heading_accum / weight_accum

		#顯示出粒子的平均加總位置
        turtle.color('orange') #它是橘色的
        turtle.setposition(x_estimate, y_estimate)
        turtle.setheading(90 - heading_estimate) #將畫筆的方向設置為90 - particle.heading。
        turtle.shape('turtle') #在畫布上以'烏龜'顯示
        turtle.stamp() #在當前烏龜位置，將烏龜形狀的副本標記在畫布上。
        turtle.update() #更新畫布

    def show_robot(self, robot):

        turtle.color('green') #它是綠色的
        turtle.shape('turtle') #在畫布上以'烏龜'顯示
        turtle.shapesize(0.7, 0.7) #設定其顯示的玩偶大小
        turtle.setposition((robot.x, robot.y))
        turtle.setheading(90 - robot.heading) #將畫筆的方向設置為90 - particle.heading。
        turtle.stamp() #在當前烏龜位置，將烏龜形狀的副本標記在畫布上。
        turtle.update() #更新畫布

    def clear_objects(self):
        turtle.clearstamps() #刪掉所有戳記(all物品除了maze)


class Particle(object):

    def __init__(self, x, y, maze, heading = None, weight = 1.0, sensor_limit = None, noisy = False):

        if heading is None: #給particle一個隨機的heading方向
            heading = np.random.uniform(0,360)

        self.x = x
        self.y = y
        self.heading = heading
        self.weight = weight #給每個particle附上weight(resampling會用到)
        self.maze = maze
        self.sensor_limit = sensor_limit #傳感器的距離上限

        if noisy: # When noisy = true
            std = max(self.maze.grid_height, self.maze.grid_width) * 0.2 # 設定 noist可在的上下界

			#add_noise()：給予有誤差的座標
            self.x = self.add_noise(x = self.x, std = std)
            self.y = self.add_noise(x = self.y, std = std)
            self.heading = self.add_noise(x = self.heading, std = 360 * 0.05) #改應heading的位置(x)跟方向

        self.fix_invalid_particles() #修復無效粒子


    def fix_invalid_particles(self):

        # Fix invalid particles
        if self.x < 0: #算出負的無效
            self.x = 0
        if self.x > self.maze.width:  #算出小於maze寬度的無效
            self.x = self.maze.width * 0.9999
        if self.y < 0:
            self.y = 0
        if self.y > self.maze.height:  #算出小於maze高度的無效
            self.y = self.maze.height * 0.9999
        '''
        if self.heading > 360:
            self.heading -= 360
        if self.heading < 0:
            self.heading += 360
        '''
        self.heading = self.heading % 360 #這樣就一定不會超過360

    @property
    def state(self): #回傳當前狀態

        return (self.x, self.y, self.heading)

    def add_noise(self, x, std): #回傳加好noise的位置

        return x + np.random.normal(0, std) #給有一點誤差的x

    def read_sensor(self, maze): #感測環境(烏龜的前，後，左和右安裝了四個傳感器。)

        readings = maze.distance_to_walls(coordinates = (self.x, self.y)) #傳感器在四周(上下左右)測量與最近壁的垂直距離

        heading = self.heading % 360 #確保heading角度不超過360

        # Remove the compass from particle *從粒子上取下指南針(幫忙依headings數值轉方向 -> 在上方的90度偵測到一面牆=右方有一面牆)
        if heading >= 45 and heading < 135: #未超出當前角度範圍
            readings = readings
        elif heading >= 135 and heading < 225: #需要順轉一格
            readings = readings[-1:] + readings[:-1]
            #readings = [readings[3], readings[0], readings[1], readings[2]] -> 重新排序(:-1除最後一個取全部 -1倒數第一個的意思)
        elif heading >= 225 and heading < 315: #需要順轉兩格
            readings = readings[-2:] + readings[:-2]
            #readings = [readings[2], readings[3], readings[0], readings[1]] -> 重新排序
        else: #需要順轉三格
            readings = readings[-3:] + readings[:-3]
            #readings = [readings[1], readings[2], readings[3], readings[0]] -> 重新排序

        if self.sensor_limit is not None: #if有限制感測距離上限
            for i in range(len(readings)): #針對每個readings
                if readings[i] > self.sensor_limit: #偵測距離有大於給定上限的，距離重設為上限的數值
                    readings[i] = self.sensor_limit

        return readings #返回獲得的感測數據

    def try_move(self, speed, maze, noisy = False): # move裡會使用到的函式

		#給定heading方向跟heading角度、radians弧度
        heading = self.heading
        heading_rad = np.radians(heading) #角度轉弧度

		 #方向乘上移動速度就是等等要移動的距離
        dx = np.sin(heading_rad) * speed
        dy = np.cos(heading_rad) * speed

		#下一步
        x = self.x + dx
        y = self.y + dy

		#原位置//格子寬高 -> 等等要判斷是否再格子裡甚麼的
        gj1 = int(self.x // maze.grid_width)
        gi1 = int(self.y // maze.grid_height)
		#新位置//格子寬高 -> 等等要判斷是否再格子裡甚麼的
        gj2 = int(x // maze.grid_width)
        gi2 = int(y // maze.grid_height)

        # Check if the particle is still in the maze 確認移動後粒子是否還在迷宮中
        if gi2 < 0 or gi2 >= maze.num_rows or gj2 < 0 or gj2 >= maze.num_cols:
            return False

        # Move in the same grid #if是在同網格中的移動(直接移)
        if gi1 == gi2 and gj1 == gj2:
            self.x = x
            self.y = y
            return True
        # Move across one grid vertically
        elif abs(gi1 - gi2) == 1 and abs(gj1 - gj2) == 0:#if是要垂直的移動到不同網格
            if maze.maze[min(gi1, gi2), gj1] & 4 != 0: #旁邊有牆就不能移
                return False
            else: #旁邊沒牆才可以移
                self.x = x
                self.y = y
                return True
        # Move across one grid horizonally
        elif abs(gi1 - gi2) == 0 and abs(gj1 - gj2) == 1:#if是要水平的移動到不同網格
            if maze.maze[gi1, min(gj1, gj2)] & 2 != 0:#旁邊有牆就不能移
                return False
            else: #旁邊沒牆才可以移
                self.x = x
                self.y = y
                return True
        # Move across grids both vertically and horizonally
        elif abs(gi1 - gi2) == 1 and abs(gj1 - gj2) == 1: #if是要水平+垂直的移動到不同網格

			#計算要移動的水平距離
            x0 = max(gj1, gj2) * maze.grid_width
            y0 = (y - self.y) / (x - self.x) * (x0 - self.x) + self.y

            if maze.maze[int(y0 // maze.grid_height), min(gj1, gj2)] & 2 != 0:#旁邊有牆就不能移
                return False

			#計算要移動的垂直距離
            y0 = max(gi1, gi2) * maze.grid_height
            x0 = (x - self.x) / (y - self.y) * (y0 - self.y) + self.x

            if maze.maze[min(gi1, gi2), int(x0 // maze.grid_width)] & 4 != 0:#旁邊有牆就不能移
                return False

			 #旁邊沒牆才可以移
            self.x = x
            self.y = y
            return True

        else:#都不是上述情況的話就是erro
            raise Exception('Unexpected collision detection.')


class Robot(Particle):

	#初始化機器人
    def __init__(self, x, y, maze, heading = None, speed = 1.0, sensor_limit = None, noisy = True):

        super(Robot, self).__init__(x = x, y = y, maze = maze, heading = heading, sensor_limit = sensor_limit, noisy = noisy)
        self.step_count = 0
        self.noisy = noisy
        self.time_step = 0
        self.speed = speed

    def choose_random_direction(self): #決定初始的前往方向(隨機)

        self.heading = np.random.uniform(0, 360) #np.random.uniform()：浮點、any value within the given interval is equally likely to be drawn by uniform.(抽到的機率均等)

    def add_sensor_noise(self, x, z = 0.05): #替sensor加上誤差以製造noise

        readings = list(x) # 將sensing資訊放入一個list

        for i in range(len(readings)):
            std = readings[i] * z / 2 #製造一個add noise的上限
            readings[i] = readings[i] + np.random.normal(0, std) #將readings加上np.random.normal(0, std)來混淆/加上誤差

        return readings

    def read_sensor(self, maze):

        # Robot has error in reading the sensor while particles do not. 機器人在讀取感測資訊時會有誤差，但粒子不會(*預設)

		#遞迴呼叫read_sensor()
        readings = super(Robot, self).read_sensor(maze = maze) #super()：用於調用父類(超類)的一個方法，是用來解決多重繼承問題的

        if self.noisy == True: #if init設定為true：
            readings = self.add_sensor_noise(x = readings) #利用add_sensor_noise()來增加雜訊/誤差

        return readings #回傳處理好的、有誤差的readings(for Robot, particles的沒有)

    def move(self, maze): #物體的移動(決定下一步)

        while True:
            self.time_step += 1 #時間++
            if self.try_move(speed = self.speed, maze = maze, noisy = False): #呼叫上方函式try_move()
                break
            self.choose_random_direction()  #決定初始的前往方向(隨機)


class WeightedDistribution(object): #Resampling 會用到

    def __init__(self, particles):

        accum = 0.0 #初始化accum，計算weight總和
        self.particles = particles #初始化物件(下面會用)
        self.distribution = list() #初始化物件(下面會用)
        for particle in self.particles: #讓每個particle跑for迴圈
            accum += particle.weight #計算weight總和
            self.distribution.append(accum) #將weight總和插入distribution(add)

    def random_select(self): #Resampling 會用到

        try:
			# 回傳一個特定的particle(在particles[bisect_left()回傳的插入位置])，隨機選取的
            return self.particles[bisect.bisect_left(self.distribution, np.random.uniform(0, 1))] #bisect_left()：陣列二分演算法，回傳的插入位置會在所有 self.distribution 當中的 np.random.uniform(0, 1)<隨機出的值> 的前面（左邊）
																		#np.random.uniform()：浮點、any value within the given interval is equally likely to be drawn by uniform.(抽到的機率均等)
        except IndexError: # 錯誤(沒有weight不能依weight的權重做Resample)#np.random.uniform()：浮點、any value within the given interval is equally likely to be drawn by uniform.(抽到的機率均等)
            # When all particles have weights zero
            return None

def euclidean_distance(x1, x2): # 計算歐式距離 ex.兩點a(x1,y1)與b(x2,y2)的歐式距離 = [(x1-x2)^2+(y1-y2)^2]^1/2

    return np.linalg.norm(np.asarray(x1) - np.asarray(x2)) # 計算出兩array相應點之標準距離

def weight_gaussian_kernel(x1, x2, std = 10):

    distance = euclidean_distance(x1 = x1, x2 = x2) # 計算歐式距離：是在m維空間中兩個點之間的真實距離。
    return np.exp(-distance ** 2 / (2 * std)) # 取指數算出particle's weight & 返回







