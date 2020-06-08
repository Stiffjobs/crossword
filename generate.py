import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.domains.keys():
            to_delete = []
            for word in self.domains[var]:
                if var.length != len(word):
                    to_delete.append(word)
            for val in to_delete:
                self.domains[var].remove(val)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        Overlaps = self.crossword.overlaps[x, y]
        if Overlaps == None:
            return revised
        else:
            i, j = Overlaps
            change = []
            for wordx in self.domains[x]:
                exist = False
                for wordy in self.domains[y]:
                    if wordx[i] == wordy[j]:
                        exist = True
                if exist == False:
                    change.append(wordx)
                    revised = True
            for Change in change:
                if self.domains[x] != None:
                    self.domains[x].remove(Change)

            return revised

    def dequeue(self, queue):
        for i, j in queue:
            queue.remove((i, j))
            return i, j

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue = []
        if arcs == None:
            for i in self.domains.keys():
                for j in self.domains.keys():
                    if i != j:
                        queue.append((i, j))
        else:
            queue = arcs[:]

        while len(queue) != 0:
            x, y = self.dequeue(queue)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for z in self.crossword.neighbors(x):
                    if z != y:
                        queue.append((z, x))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for var in self.domains.keys():
            if var not in assignment:
                return False
            else:
                if assignment[var] == None:
                    return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        constraints = []

        for key, value in assignment.items():
            if value in constraints:
                return False
            else:
                constraints.append(value)
            
            if key.length != len(value):
                return False
            
            neighbors = self.crossword.neighbors(key)
            for neighbor in neighbors:
                val_i, neigh_j = self.crossword.overlaps[key, neighbor]
                if neighbor in assignment:
                    if assignment[neighbor][neigh_j] != value[val_i]:
                        return False
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        ordering = {}
        values = self.domains[var]
        neighbors = self.crossword.neighbors(var)
        for val in values:
            if val in assignment:
                continue
            else:
                count = 0
                for neighbor in neighbors:
                    if val in self.domains[neighbor]:
                        count += 1
                ordering[val] = count
        return sorted(ordering, key=lambda k: ordering[k])

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        value = 1000000000000
        degree = 0
        for i in self.domains.keys():
            if i in assignment:
                continue
            else:
                if value > len(self.domains[i]):
                    var = i
                    value = len(self.domains[i])
                    if self.crossword.neighbors(i) != None:
                        degree = len(self.crossword.neighbors(i))
                    else:
                        degree = 0
                elif value == len(self.domains[i]):
                    if self.crossword.neighbors(i) != None:
                        if degree < len(self.crossword.neighbors(i)):
                            var = i
                            value = len(self.domains[i])
                            degree = len(self.crossword.neighbors(i))
                    else:
                        var = i
                        degree = 0
        return var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result != False:
                    return result
            assignment.pop(var)
            
        return False


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
