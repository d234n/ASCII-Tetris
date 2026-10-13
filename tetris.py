import curses
import random
import time

width = 10
height = 20

shapes = [
    [(0,1),(1,1),(2,1),(3,1)], # I
    [(1,0),(2,0),(1,1),(2,1)], # O
    [(1,0),(0,1),(1,1),(2,1)], # T
    [(1,0),(2,0),(0,1),(1,1)], # S
    [(0,0),(1,0),(1,1),(2,1)], # Z
    [(0,0),(0,1),(1,1),(2,1)], # J
    [(2,0),(0,1),(1,1),(2,1)], # L
]

block_symbols = ["[]", "55", "ZZ", "EE", "HH", "MM", "FF", "##"]

def rotate(shape):
    return [(3 - y, x) for x, y in shape]

def can_move(board, shape, x, y):
    for dx, dy in shape:
        nx = x + dx
        ny = y + dy

        if nx < 0 or nx >= width or ny >= height:
            return False

        if ny >= 0 and board[ny][nx]:
            return False

    return True

def clear_lines(board):
    remaining = [
        row for row in board if not all(row)
    ]
    cleared = height - len(remaining)

    while len(remaining) < height:
        remaining.insert(0, [0] * width)

    board[:] = remaining
    return cleared

def setup_colors():
    if not curses.has_colors():
        return {}

    try:
        curses.start_color()
        purple = 129 if curses.COLORS >= 256 else curses.COLOR_MAGENTA
        orange = 208 if curses.COLORS >= 256 else curses.COLOR_YELLOW
    except curses.error:
        return {}

    try:
        curses.use_default_colors()
        background = -1
    except curses.error:
        background = curses.COLOR_BLACK

    palette = [
        curses.COLOR_CYAN,
        curses.COLOR_YELLOW,
        curses.COLOR_GREEN,
        curses.COLOR_RED,
        curses.COLOR_BLUE,
        purple,
        orange,
    ]

    color_pairs = {}
    try:
        for pair_id, symbol in enumerate(block_symbols, start=1):
            color = palette[(pair_id - 1) % len(palette)]
            curses.init_pair(pair_id, color,background)
            color_pairs[symbol] = pair_id
    except curses.error:
        return {}

    return color_pairs

def draw(stdscr, board, shape, x, y, score, block_symbol, colored_mode, color_pairs):
    stdscr.erase()

    stdscr.addstr(0, 2, "ASCII TETRIS")
    stdscr.addstr(1, 2, f"Score: {score} | color: {'ON' if colored_mode else 'OFF'}")

    # Gambar border papan.
    stdscr.addstr(2, 2, "+" + "--" * width + "+")

    for row in range(height):
        stdscr.addstr(3 + row, 2, "|")

        for col in range(width):
            cell = board[row][col]

            for dx, dy in shape:
                if x + dx == col and y + dy == row:
                    cell = block_symbol
                    break

            attribute = curses.A_NORMAL
            if colored_mode and cell:
                attribute = curses.color_pair(color_pairs[cell])

            stdscr.addstr(3 + row, 3 + col * 2, cell if cell else "  ", attribute)

        stdscr.addstr(3 + row, 3 + width * 2, "|")

    stdscr.addstr(
        3 + height, 2,
        "#" + "%#" * width + "%"
    )
    stdscr.addstr(
        5 + height, 2,
        "Left/Right: move | Up: rotate"
    )
    stdscr.addstr(
        6 + height, 2,
        "Down: faster | Space: drop | Q: quit"
    )

    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(True)

    board = [[""] * width for _ in range(height)]
    score = 0
    game_over = False

    shape = random.choice(shapes)
    block_symbol = random.choice(block_symbols)
    x, y = 3, 0

    last_fall = time.monotonic()
    fall_delay = 0.5

    color_pairs = setup_colors()
    colored_mode = False

    while not game_over:
        rows, cols = stdscr.getmaxyx()

        if rows < height + 7 or cols < 38:
            stdscr.erase()
            stdscr.addstr(0, 0, f"Terminal terbaca: {rows} baris x {cols} kolom")
            stdscr.addstr(1, 0, "Kirim angka ukuran terminal ini.")
            stdscr.refresh()
            time.sleep(0.1)
            continue

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            break

        elif key in (ord("c"), ord("C")) and color_pairs:
            colored_mode = not colored_mode

        # Gerakan ke kiri & kanan.
        if key == curses.KEY_LEFT:
            if can_move(board, shape, x - 1, y):
                x -= 1

        elif key == curses.KEY_RIGHT:
            if can_move(board, shape, x + 1, y):
                x += 1

        # Putar block.
        elif key == curses.KEY_UP:
            rotated = rotate(shape)
            if can_move(board, rotated, x, y):
                shape = rotated

        # Percepat jatuh.
        elif key == curses.KEY_DOWN:
            if can_move(board, shape, x, y + 1):
                y += 1

        # Jatuhkan block langsung ke bawah.
        elif key == ord(" "):
            while can_move(board, shape, x, y +1):
                y += 1
            last_fall = 0

        # Gravitasi.
        now = time.monotonic()

        if now - last_fall >= fall_delay:
            if can_move(board, shape, x, y + 1):
                y += 1
            else:

                # Block sudah mendarat. Simpan ke papan.
                for dx, dy in shape:
                    nx = x + dx
                    ny = y + dy

                    if 0 <= ny < height:
                        board[ny][nx] = block_symbol

                cleared = clear_lines(board)
                score += cleared * 100

                # Buat block baru.
                shape = random.choice(shapes)
                block_symbol = random.choice(block_symbols)
                x, y = 3, 0

                if not can_move(board, shape, x, y):
                    game_over = True

            last_fall = now

        draw(stdscr, board, shape, x, y, score, block_symbol, colored_mode, color_pairs)
        time.sleep(0.03)

    # Tampilkan pesan akhir.
    stdscr.nodelay(False)
    stdscr.erase()
    stdscr.addstr(2, 2, "GAME OVER!")
    stdscr.addstr(4, 2, f"Final score: {score}")
    stdscr.addstr(6, 2, "Tekan tombol apa saja untuk keluar.")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)                            