# player/player.py

class Player:
    def __init__(self, start_row=0, start_col=0):
        self.row = start_row
        self.col = start_col

    def get_position(self):
        return (self.row, self.col)

    def move(self, direction, grid):
        """
        Move player if no wall in that direction
        """

        current_cell = grid.get_cell(self.row, self.col)

        if direction == "up":
            if not current_cell.walls["top"]:
                self.row -= 1

        elif direction == "down":
            if not current_cell.walls["bottom"]:
                self.row += 1

        elif direction == "left":
            if not current_cell.walls["left"]:
                self.col -= 1

        elif direction == "right":
            if not current_cell.walls["right"]:
                self.col += 1

    def can_move(self, direction, grid):
        """
        Check if movement is possible (used later for BFS/CSP)
        """
        current_cell = grid.get_cell(self.row, self.col)

        if direction == "up":
            return not current_cell.walls["top"]

        elif direction == "down":
            return not current_cell.walls["bottom"]

        elif direction == "left":
            return not current_cell.walls["left"]

        elif direction == "right":
            return not current_cell.walls["right"]

        return False