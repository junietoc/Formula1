import tkinter as tk
from tkinter import messagebox

# Constantes para el tablero
BOARD_SIZE = 8
SQUARE_SIZE = 60
PIECES = {
    'bR': '\u265C', 'bN': '\u265E', 'bB': '\u265D', 'bQ': '\u265B', 'bK': '\u265A', 'bP': '\u265F',
    'wR': '\u2656', 'wN': '\u2658', 'wB': '\u2657', 'wQ': '\u2655', 'wK': '\u2654', 'wP': '\u2659',
    '  ': ''
}

# Posición inicial de las piezas
START_POSITION = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP'] * 8,
    ['  '] * 8,
    ['  '] * 8,
    ['  '] * 8,
    ['  '] * 8,
    ['wP'] * 8,
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
]

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Ajedrez en Tkinter')
        self.canvas = tk.Canvas(root, width=BOARD_SIZE*SQUARE_SIZE, height=BOARD_SIZE*SQUARE_SIZE)
        self.canvas.pack()
        self.selected = None
        self.turn = 'w'  # Empiezan las blancas
        self.moved = {'wK': False, 'bK': False, 'wR0': False, 'wR7': False, 'bR0': False, 'bR7': False}
        self.board = [row[:] for row in START_POSITION]
        self.draw_board()
        self.canvas.bind('<Button-1>', self.on_click)

    def draw_board(self):
        self.canvas.delete('all')
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                color = '#F0D9B5' if (i + j) % 2 == 0 else '#B58863'
                x1, y1 = j*SQUARE_SIZE, i*SQUARE_SIZE
                x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='black')
                piece = self.board[i][j]
                if piece.strip():
                    self.canvas.create_text(x1+SQUARE_SIZE//2, y1+SQUARE_SIZE//2, text=PIECES[piece], font=('Arial', 32))
        if self.selected:
            i, j = self.selected
            x1, y1 = j*SQUARE_SIZE, i*SQUARE_SIZE
            x2, y2 = x1+SQUARE_SIZE, y1+SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=3)
        turn_text = 'Turno: Blancas' if self.turn == 'w' else 'Turno: Negras'
        self.canvas.create_text(BOARD_SIZE*SQUARE_SIZE//2, BOARD_SIZE*SQUARE_SIZE+20, text=turn_text, font=('Arial', 16))

    def is_in_check(self, color):
        # Busca el rey
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == color+'K':
                    king_pos = (r, c)
        # ¿Alguna pieza enemiga puede capturar al rey?
        enemy = 'b' if color == 'w' else 'w'
        for r in range(8):
            for c in range(8):
                if self.board[r][c].startswith(enemy):
                    if self.is_valid_move(r, c, king_pos[0], king_pos[1], ignore_check=True):
                        return True
        return False

    def is_valid_move(self, from_row, from_col, to_row, to_col, ignore_check=False):
        piece = self.board[from_row][from_col]
        target = self.board[to_row][to_col]
        if piece == '  ':
            return False
        color = piece[0]
        target_color = target[0] if target.strip() else None
        if target_color == color:
            return False  # No puede capturar sus propias piezas
        dr, dc = to_row - from_row, to_col - from_col
        abs_dr, abs_dc = abs(dr), abs(dc)
        # Peón
        if piece[1] == 'P':
            direction = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            if dc == 0 and target == '  ':
                if dr == direction:
                    return True
                if from_row == start_row and dr == 2*direction and self.board[from_row+direction][from_col] == '  ':
                    return True
            if abs_dc == 1 and dr == direction and target != '  ':
                return True
            return False
        # Torre
        if piece[1] == 'R':
            if dr == 0 or dc == 0:
                return self.is_clear_path(from_row, from_col, to_row, to_col)
            return False
        # Caballo
        if piece[1] == 'N':
            return (abs_dr, abs_dc) in [(2, 1), (1, 2)]
        # Alfil
        if piece[1] == 'B':
            if abs_dr == abs_dc:
                return self.is_clear_path(from_row, from_col, to_row, to_col)
            return False
        # Reina
        if piece[1] == 'Q':
            if dr == 0 or dc == 0 or abs_dr == abs_dc:
                return self.is_clear_path(from_row, from_col, to_row, to_col)
            return False
        # Rey
        if piece[1] == 'K':
            if max(abs_dr, abs_dc) == 1:
                # No permitir moverse a jaque
                if ignore_check:
                    return True
                temp = self.board[to_row][to_col]
                self.board[to_row][to_col] = piece
                self.board[from_row][from_col] = '  '
                in_check = self.is_in_check(color)
                self.board[from_row][from_col] = piece
                self.board[to_row][to_col] = temp
                return not in_check
            return False
        return False

    def is_clear_path(self, from_row, from_col, to_row, to_col):
        dr = (to_row - from_row)
        dc = (to_col - from_col)
        step_r = (dr > 0) - (dr < 0)
        step_c = (dc > 0) - (dc < 0)
        r, c = from_row + step_r, from_col + step_c
        while (r, c) != (to_row, to_col):
            if self.board[r][c] != '  ':
                return False
            r += step_r
            c += step_c
        return True

    def move_piece(self, from_row, from_col, to_row, to_col):
        piece = self.board[from_row][from_col]
        # Enroque
        if piece[1] == 'K' and from_row == to_row and abs(to_col - from_col) == 2:
            if self.can_castle(piece[0], from_row, from_col, to_row, to_col):
                # Verifica que el rey no pase por jaque
                step = 1 if to_col > from_col else -1
                for offset in range(0, 3):
                    col = from_col + offset*step
                    temp = self.board[from_row][col]
                    self.board[from_row][col] = piece
                    self.board[from_row][from_col] = '  '
                    if self.is_in_check(piece[0]):
                        self.board[from_row][from_col] = piece
                        self.board[from_row][col] = temp
                        messagebox.showinfo('Movimiento inválido', 'No se puede enrocar pasando por jaque.')
                        return False
                    self.board[from_row][from_col] = piece
                    self.board[from_row][col] = temp
                self.do_castle(piece[0], from_row, from_col, to_row, to_col)
                return True
            else:
                messagebox.showinfo('Movimiento inválido', 'No se puede realizar el enroque.')
                return False
        # Movimiento normal
        if self.is_valid_move(from_row, from_col, to_row, to_col):
            # Simula el movimiento para evitar dejar al rey en jaque
            temp = self.board[to_row][to_col]
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = '  '
            if self.is_in_check(piece[0]):
                self.board[from_row][from_col] = piece
                self.board[to_row][to_col] = temp
                messagebox.showinfo('Movimiento inválido', 'No puedes dejar a tu rey en jaque.')
                return False
            # Promoción de peón
            if piece[1] == 'P' and (to_row == 0 or to_row == 7):
                self.board[to_row][to_col] = piece[0]+'Q'
            # Marcar piezas movidas para enroque
            if piece[1] == 'K':
                self.moved[piece[0]+'K'] = True
            if piece[1] == 'R':
                if from_col == 0:
                    self.moved[piece[0]+'R0'] = True
                if from_col == 7:
                    self.moved[piece[0]+'R7'] = True
            return True
        else:
            messagebox.showinfo('Movimiento inválido', 'Ese movimiento no es válido según las reglas del ajedrez.')
            return False

    def can_castle(self, color, from_row, from_col, to_row, to_col):
        if self.moved[color+'K']:
            return False
        if to_col > from_col:
            rook_col = 7
            rook_key = color+'R7'
        else:
            rook_col = 0
            rook_key = color+'R0'
        if self.moved[rook_key]:
            return False
        # Casillas entre rey y torre deben estar vacías
        step = 1 if to_col > from_col else -1
        for c in range(from_col + step, rook_col, step):
            if self.board[from_row][c] != '  ':
                return False
        # (Opcional: verificar que el rey no pase por jaque)
        return True

    def do_castle(self, color, from_row, from_col, to_row, to_col):
        # Mueve el rey
        self.board[to_row][to_col] = self.board[from_row][from_col]
        self.board[from_row][from_col] = '  '
        # Mueve la torre
        if to_col > from_col:
            rook_from = 7
            rook_to = to_col - 1
        else:
            rook_from = 0
            rook_to = to_col + 1
        self.board[from_row][rook_to] = self.board[from_row][rook_from]
        self.board[from_row][rook_from] = '  '
        # Marcar piezas movidas
        self.moved[color+'K'] = True
        if rook_from == 0:
            self.moved[color+'R0'] = True
        else:
            self.moved[color+'R7'] = True

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        for r1 in range(8):
            for c1 in range(8):
                if self.board[r1][c1].startswith(color):
                    for r2 in range(8):
                        for c2 in range(8):
                            temp = self.board[r2][c2]
                            piece = self.board[r1][c1]
                            if self.is_valid_move(r1, c1, r2, c2):
                                self.board[r2][c2] = piece
                                self.board[r1][c1] = '  '
                                if not self.is_in_check(color):
                                    self.board[r1][c1] = piece
                                    self.board[r2][c2] = temp
                                    return False
                                self.board[r1][c1] = piece
                                self.board[r2][c2] = temp
        return True

    def is_stalemate(self, color):
        if self.is_in_check(color):
            return False
        for r1 in range(8):
            for c1 in range(8):
                if self.board[r1][c1].startswith(color):
                    for r2 in range(8):
                        for c2 in range(8):
                            temp = self.board[r2][c2]
                            piece = self.board[r1][c1]
                            if self.is_valid_move(r1, c1, r2, c2):
                                self.board[r2][c2] = piece
                                self.board[r1][c1] = '  '
                                if not self.is_in_check(color):
                                    self.board[r1][c1] = piece
                                    self.board[r2][c2] = temp
                                    return False
                                self.board[r1][c1] = piece
                                self.board[r2][c2] = temp
        return True

    def on_click(self, event):
        row, col = event.y // SQUARE_SIZE, event.x // SQUARE_SIZE
        if row >= BOARD_SIZE or col >= BOARD_SIZE:
            return
        if self.selected:
            sel_row, sel_col = self.selected
            if (row, col) != (sel_row, sel_col):
                moved = self.move_piece(sel_row, sel_col, row, col)
                if moved:
                    # Verifica jaque mate o tablas
                    if self.is_checkmate('b' if self.turn == 'w' else 'w'):
                        messagebox.showinfo('Fin de la partida', f'¡Jaque mate! Ganaron las {"blancas" if self.turn == "w" else "negras"}.')
                        self.root.quit()
                    elif self.is_stalemate('b' if self.turn == 'w' else 'w'):
                        messagebox.showinfo('Fin de la partida', '¡Tablas por ahogado!')
                        self.root.quit()
                    self.turn = 'b' if self.turn == 'w' else 'w'
            self.selected = None
        else:
            piece = self.board[row][col]
            if piece.strip() and piece[0] == self.turn:
                self.selected = (row, col)
            elif piece.strip():
                messagebox.showinfo('Turno incorrecto', f'Es el turno de las {"blancas" if self.turn == "w" else "negras"}.')
        self.draw_board()

if __name__ == '__main__':
    root = tk.Tk()
    app = ChessGUI(root)
    root.mainloop()
