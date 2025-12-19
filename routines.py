import random, math
from constant import KILOBOTS_X, KILOBOTS_Y, R3_ANIMATION

class RoutineR1:

    # ---------------------------------------------------------
    # SUBROUTINE SR1a: IDs Assignment
    # ---------------------------------------------------------
    def run_sr1a(self):
        """If I hear a neighbor with MY same ID and different randomNumber, I change mine"""

        for msg in self.inbox:
            isAdded = False
            for neighbor in self.neighbor_ids_randomNum:
                if neighbor['id'] == msg['content']['sender_id']:
                    isAdded = True
            if not isAdded:
                self.neighbor_ids_randomNum.append({
                    'id': msg['content']['sender_id'],
                    'randomNumber': msg['content']['randomNumber']
                })
            # If a hear a neighbor with my ID but different randomNumber -> choose new ID and add current to blacklist
            if (msg['content']['sender_id'] == self.my_id and msg['content']['randomNumber'] != self.randomNumber):
                self.blacklist_ids.append(self.my_id)
                new_id = random.randint(1, 255)
                while new_id in self.blacklist_ids:
                    new_id = random.randint(1, 255)
                self.my_id = new_id
            else:
                # Check the neighbor list sent by the neighbor
                for neighbor in msg['content']['neighbors']:
                    # If a neighbor of my neighbor has my ID but different randomNumber -> choose new ID and add current to blacklist
                    if neighbor['id'] == self.my_id and neighbor['randomNumber'] != self.randomNumber:
                        self.blacklist_ids.append(self.my_id)
                        new_id = random.randint(1, 255)
                        while new_id in self.blacklist_ids:
                            new_id = random.randint(1, 255)
                        self.my_id = new_id

            # Update minimum distance seen
            dist = msg['dist']
            if dist < self.min_dist_seen:
                self.min_dist_seen = dist

    # ---------------------------------------------------------
    # SUBROUTINE SR1b: Neighbor list creation
    # ---------------------------------------------------------
    def run_sr1b(self):
        """Filter neighbors based on estimated distance"""
        
        # Calculate threshold r. The paper uses r = 1.5x + 10 (in mm), we will you 0.1 instead of 10
        # In Mesa Grid, the minimum distance is 1.0 aprox. We want to include diagonals (1.41 aprox)
        # but exclude distance 2.0 aprox. A factor of 1.5 works well
        threshold_r = self.min_dist_seen * 1.5 + 0.1
        
        # Build filtered list
        for msg in self.inbox:
            if msg['dist'] <= threshold_r:
                # msg content is the neighbor's ID
                if msg['content'] not in self.neighbor_ids:
                    if not isinstance(msg['content'], dict):
                        self.neighbor_ids.append(msg['content'])
            

    # ---------------------------------------------------------
    # SUBROUTINE SR1c: Position identification
    # ---------------------------------------------------------
    def run_sr1c_collection(self):
        """Collect the number of neighbors that my neighbors have"""

        for msg in self.inbox:
            sender_id = msg['sender_id']
            # In this phase, the content of the message is the neighbor's count
            sender_count = msg['content'] 
            self.neighbor_counts[sender_id] = sender_count


    def determine_role(self):
        """Determine the role of the agent based on neighbor counts"""

        my_count = len(self.neighbor_ids)
        
        if not self.neighbor_counts:
            return 

        # Neighbor values
        neighbor_counts = list(self.neighbor_counts.values())
        min_neigh = min(neighbor_counts)
        max_neigh = max(neighbor_counts)

        # CORNER -> I have fewer neighbors than any of my neighbors
        if my_count < min_neigh:
            self.role = "CORNER"
            self.led_color = "red"  # Red color
            
        # MIDDLE -> I have more (or equal) neighbors than the maximum of my neighbors
        elif my_count >= max_neigh: 
            self.role = "MIDDLE"
            self.led_color = "green" # Green color
            
        # BORDER -> Other cases
        else:
            self.role = "BORDER"
            self.led_color = "blue"  # Blue color

        for msg in self.filter_neighbors_message():
            if isinstance(msg['content'], dict):
                neighborID = msg['content']['id']
                exist = any(d["id"] == neighborID for d in self.neighbor_roles)
                if not exist:
                    self.neighbor_roles.append({
                        'id': neighborID,
                        'role': msg['content']['role']
                    })



class RoutineR2:
    def run_sr2a_origin_assignment(self):
        """Assign origin based on received numbers"""
        
        for msg in self.filter_neighbors_message():
            received_num = msg['content']
            if isinstance(received_num, int):
                if self.role != "CORNER": 
                    if received_num is not None and received_num < self.numOriginAssigment:
                        self.numOriginAssigment = received_num
                        self.led_color = "pink"  # Pink indicates that I updated my number
                elif self.role == "CORNER":
                    if self.numOriginAssigment == received_num: # If corner receives its own number, 
                        self.led_color = "black"                # it will be the origin at the end of the phase 
                    else:
                        self.led_color = "purple"


    def setOriginAssignment(self):
        """Set origin position based on assigned number"""
        
        for msg in self.filter_neighbors_message():
            received_num = msg['content']
            if self.role != "CORNER":
               self.led_color = "gray"
            elif self.role == "CORNER":
                if self.numOriginAssigment == received_num: # If corner receives its own number,
                    self.position = [1,1]                   # it will be the origin [1,1]             
                    self.led_color = "black"
                else:
                    self.led_color = "gray"

    
    def setOriginNeighborsPosition(self):
        """Origin [1,1] sends positions to BORDER and MIDDLE neighbors"""
        
        for msg in self.filter_neighbors_message():
            if isinstance(msg['content'], list):
                for content in msg['content']:
                    if content['id'] == self.my_id:
                        self.position = content['position'] # Set my position based on the message
                        if self.position == [1,2]: # Depending on my position, set LED color
                            self.led_color = "red"
                        elif self.position == [2,1]:
                            self.led_color = "blue"
                        elif self.position == [2,2]:
                            self.led_color = "green"
            
    # ---------------------------------------------------------
    # SUBROUTINE SR2B: Rectangle dimension setting
    # ---------------------------------------------------------
    def setRecDimension(self):
        """Receive count message from neighbors"""

        # BORDER robots update their count message if they have count = 0 and have received a message
        if self.count == 0 and self.role == "BORDER" and not self.position:
            for msg in self.filter_neighbors_message():
                if msg['content'] and not ("corner_id" in msg['content']):
                    content = msg['content']
                    self.messageFromCorner = False
                    for robot in self.neighbor_roles:
                        if robot['id'] == msg["sender_id"] and robot['role'] == "CORNER":
                            self.messageFromCorner = True
                            
                    self.count = content['count'] + 1
                    self.countMessage = content
                    self.led_color = "lightblue" # Indicate that I have updated my count
        
        # The same to CORNER robots
        elif self.count == 0 and self.role == "CORNER" and not self.position:
            for msg in self.filter_neighbors_message():
                if msg['content'] and "corner_id" in msg['content']:
                    content = msg['content']
                    self.count = content['count'] + 1
                    self.countMessage = content
        
                # - Specific cases for positions [1,2] and [1,1]
        # We have to ensure that [1,2] don't update its count from [2,1], so we check the count if it is greater than 2
        elif self.position == [1,2] and self.count == 0:
            for msg in self.filter_neighbors_message():
                if msg['content'] and isinstance(msg['content'], dict):
                    content = msg['content']
                    if content['count'] > 2:
                        self.count = content['count'] + 1
                        self.countMessage = content
        
        # If count message is from [1,2] to [1,1] updates its count and the final countMessage
        elif self.position == [1,1]:
            for msg in self.filter_neighbors_message():
                if msg['content'] and isinstance(msg['content'], dict):
                    content = msg['content']
                    self.count = 1
                    if content['count'] > 2:
                        self.countMessage = content
        

    def set_relative_position(self):
        """Set relative position to BORDER and CORNER based on the final count messages"""

        # If I am [1,1], I have already the countMessage from the previous phase
        if self.position == [1,1] and self.countFullMessage is None:
            #print("Robot", self.my_id, "at [1,1] setting countFullMessage, from countMessage:", self.countMessage)
            self.countMessage["check"] = True
            self.countFullMessage = self.countMessage
        
        else:
            for msg in self.filter_neighbors_message():
                if msg['content'] and isinstance(msg['content'], dict) and "check" in msg['content']:
                    #print("Robot", self.my_id, "at", self.position, "received countFullMessage from neighbor:", msg['content'])
                    self.countFullMessage = msg['content']


        # For other BORDER or CORNER robots, set their position based on the countFullMessage and their count
        if not self.position and (self.role == "BORDER" or self.role == "CORNER") and not (self.countFullMessage is None):
            for msg in self.filter_neighbors_message():
                if msg['content'] and not ("sender_position" in msg):
                    self.countFullMessage = msg['content']

                    if self.countMessage['count'] < self.countFullMessage['C1']:
                        self.position = [self.count, 1]
                    elif self.countFullMessage['C1'] < self.count <= self.countFullMessage['C2']:
                        self.position = [self.countFullMessage['C1'], self.count - self.countFullMessage['C1'] + 1]
                    elif self.countFullMessage['C2'] < self.count <= self.countFullMessage['C3']:
                        self.position = [self.countFullMessage['C1'] - (self.count - self.countFullMessage['C2']), self.countFullMessage['C2'] - self.countFullMessage['C1'] + 1]
                    else:
                        self.position = [1, (self.countFullMessage['C2'] - self.countFullMessage['C1'] + 1) - (self.count - self.countFullMessage['C3'])]
                   

    # ---------------------------------------------------------
    # SUBROUTINE SR2C: Position setting
    # ---------------------------------------------------------
    def set_global_position(self):
        """Set global position to MIDDLE robots based on neighbors' positions"""

        self.led_color = "lightgreen"

        # If I am MIDDLE and I don't have position yet, check neighbors' positions to determine mine
        if not self.position and self.role == "MIDDLE":
            neighbors_positions = []
            for msg in self.filter_neighbors_message():
                if msg['content'] and isinstance(msg['content'], list):
                    neighbors_positions.append(msg['content'])
            if neighbors_positions:
                # Check if I can determine my position (coordinates x or y) based on neighbors' positions
                self.check_position(neighbors_positions)

                # If x or y in auxPosition is set, update my position
                if self.auxPosition[0] != -1 and self.auxPosition[1] != -1:
                    self.position = self.auxPosition


class RoutineR3:
    def set_animation_sincronization(self):
        if not self.position or self.position == [-1, -1]:
            self.led_color = "grey"
            return

        # Calculate the start time of the animation for this kilobot
        start_time = 480
        
        # Calculate how much time has passed since the start of the animation
        elapsed = self.internal_clock - start_time

        # Define the color pattern
        pattern_colors = ["green", "blue", "pink", "orange", "white"]

        # PHASE 0: First 2 ticks (0 and 1) -> All RED
        if elapsed < 2:
            self.led_color = "red"

        # PHASE 1: Next 2 ticks (2 and 3) -> By COLUMNS
        elif elapsed < 4:
            x = self.position[0]
            color_index = (x - 1) % 5
            self.led_color = pattern_colors[color_index]

        # PHASE 2: From tick 4 onwards -> By ROWS (and stays that way)
        else:
            y = self.position[1]
            color_index = (y - 1) % 5
            self.led_color = pattern_colors[color_index]
            


    def set_role_color(self):
        """Choose the function to display"""
        if R3_ANIMATION == "smiley_face":
            self.smiley_face() # 10x10
        elif R3_ANIMATION == "diagonal_wave":
            self.setDiagonalWaveAnimation() # Any size
        elif R3_ANIMATION == "wasp":
            self.setWaspAnimation() # 30x30
    
    def smiley_face(self):
        """
        Displays a static smiley face on a 10x10 grid.
        Requires self.position to have values between [1,1] and [10,10].
        """

        # Check if position is valid
        if not self.position or self.position == [-1, -1]:
            self.led_color = "grey"
            return

        # Definition of the coordinates that form the face.
        # Format: [column (X), row (Y)]
        smiley_pixels = [
            # --- Eyes ---
            [3, 8], [8, 8], 
            [3, 7], [8, 7], 
            
            # --- Mouth ---
            [1, 5], [10, 5], # Extreme corners
            [2, 4], [9, 4],  # Middle part of the smile
            [3, 3], [4, 3], [5, 3], [6, 3], [7, 3], [8, 3] # Lower part
        ]

        # Turn on LED if my position is in smiley pixels
        if self.position in smiley_pixels:
            self.led_color = "yellow" # Face color (on)
        else:
            self.led_color = "black"  # Background (off)


    def setDiagonalWaveAnimation(self):
        """
        Creates a diagonal wave of colors that moves across the swarm.
        Works for ANY grid size (indeterminate).
        """
        # Safety check: if I don't have a position yet, turn grey
        if not self.position or self.position == [-1, -1]:
            self.led_color = "grey"
            return

        # Get coordinates
        x = self.position[0]
        y = self.position[1]

        # --- ANIMATION PARAMETERS ---
        # Speed: How fast the wave moves (lower numbers = slower)
        # Try 0.2 for slow, 0.5 for fast.
        speed = 0.2
        
        # Width: How wide the color bands are (in number of robots)
        band_width = 5.0 
        
        # Define the cyclic color palette
        colors = ["red", "orange", "yellow"]

        # --- MATHEMATICAL CALCULATION ---
        # Sum x + y to get constant diagonals.
        #    (Robots with the same x+y value form a diagonal line /).
        # Subtract time (internal_clock * speed) to make the wave move over time.
        val = (x + y) - (self.internal_clock * speed)

        # Map the value to the index of the color list.
        #    Use the modulo operator (%) to make the pattern repeat infinitely.
        color_index = int(val / band_width) % len(colors)

        # Assign the calculated color
        self.led_color = colors[color_index]


    def setWaspAnimation(self):
        """
        Draws a wasp with a striped abdomen and moving wings.
        Designed for a 30x30 grid.
        """
        if not self.position or self.position == [-1, -1]:
            self.led_color = "grey"
            return

        # Coordinate adjustment (1-based -> 0-based)
        # Invert Y to draw visually from top to bottom
        grid_x = self.position[0] - 1 
        grid_y = 29 - (self.position[1] - 1)

        # MAP LEGEND:
        # . = Sky (Light blue)
        # H = Head / Antennae (Black)
        # T = Thorax (Black)
        # Y = Yellow (Abdomen/Body)
        # B = Black (Abdomen stripes/Stinger)
        # 1 = Wings State 1 (Extended)
        # 2 = Wings State 2 (Contracted)
        
        wasp_sprite = [
            "..............................", # 0
            ".....H..................H.....", # 1 Antennae
            "......H................H......", # 2
            ".......H..............H.......", # 3
            "........HH..........HH........", # 4
            ".........HHHHHHHHHHHH.........", # 5 Head
            ".........HHHHHHHHHHHH.........", # 6
            "..........HHHHHHHHHH..........", # 7
            "111.......TTTTTTTTTT.......111", # 8 Neck / Start Wings 1
            ".1111.....TTTTTTTTTT.....1111.", # 9 Thorax
            "..11111...TTTTTTTTTT...11111..", # 10
            "...11111..TTTTTTTTTT..11111...", # 11
            "....222....YYYYYYYY....222....", # 12 Wasp waist / Wings 2
            ".....222..YYYYYYYYYY..222.....", # 13 Abdomen start
            "......22..BBBBBBBBBB..22......", # 14 Black Stripe
            "..........BBBBBBBBBB..........", # 15
            "..........YYYYYYYYYY..........", # 16 Yellow Stripe
            "..........YYYYYYYYYY..........", # 17
            "...........BBBBBBBB...........", # 18 Black Stripe
            "...........BBBBBBBB...........", # 19
            "...........YYYYYYYY...........", # 20 Yellow Stripe
            "............YYYYYY............", # 21
            "............BBBBBB............", # 22 Black Stripe
            ".............BBBB.............", # 23
            ".............YYYY.............", # 24 Yellow Stripe
            "..............YY..............", # 25
            "..............BB..............", # 26 Stinger base
            "..............BB..............", # 27
            "...............B..............", # 28 Stinger tip
            ".............................."  # 29
        ]

        # --- ANIMATION LOGIC ---
        # Wasps beat their wings very fast.
        # speed = 2 means it changes every 2 ticks.
        anim_speed = 2
        phase = (self.internal_clock // anim_speed) % 2

        # --- RENDERING ---
        try:
            pixel = wasp_sprite[grid_y][grid_x]
        except IndexError:
            self.led_color = "lightblue"
            return

        # Colors
        sky_color = "lightblue"
        black_color = "black"
        yellow_color = "yellow" # Or "gold" if supported
        wing_color = "white"    # Or "lightgrey"

        if pixel == '.':
            self.led_color = sky_color
            
        elif pixel == 'H' or pixel == 'T' or pixel == 'B':
            self.led_color = black_color
            
        elif pixel == 'Y':
            self.led_color = yellow_color

        # --- WING ANIMATION ---
        elif pixel == '1': # Wings open
            if phase == 0:
                self.led_color = wing_color
            else:
                self.led_color = sky_color # Invisible

        elif pixel == '2': # Wings closed
            if phase == 1:
                self.led_color = wing_color
            else:
                self.led_color = sky_color # Invisible

