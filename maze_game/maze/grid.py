# maze/grid.py

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col

        # Each cell has 4 walls
        self.walls = {
            "top": True,
            "bottom": True,
            "left": True,
            "right": True
        }

        self.visited = False


class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        self.cells = [
            [Cell(r, c) for c in range(cols)]
            for r in range(rows)
        ]

    def get_cell(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.cells[row][col]
        return None

    def get_unvisited_neighbors(self, cell):
        directions = [
            ("top", cell.row - 1, cell.col),
            ("bottom", cell.row + 1, cell.col),
            ("left", cell.row, cell.col - 1),
            ("right", cell.row, cell.col + 1),
        ]

        neighbors = []

        for direction, r, c in directions:
            neighbor = self.get_cell(r, c)
            if neighbor and not neighbor.visited:
                neighbors.append((direction, neighbor))

        return neighbors