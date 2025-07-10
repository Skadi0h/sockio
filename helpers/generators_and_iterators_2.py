import tkinter as tk
from collections.abc import Generator


def colour_generator(
    initial_color: str,
    trigger_color: str | None = None
) -> Generator[str]:
    yield initial_color
    color = trigger_color or initial_color
    while True:
        yield "yellow"
        color = "green" if color == "red" else "red"
        yield color
       
        
def save_colour(color: str) -> None:
    with open('workfile', 'w', encoding="utf-8") as f:
        f.write(color)


def read_color() -> str:
    with open('workfile', mode="r", encoding="utf-8") as f:
        value = f.read()
    return value


def enable_lamp(
    lamp_number: int,
    color: str,
    lamps: list[int],
    canvas: tk.Canvas
) -> None:
    
    current_lamp = lamps[lamp_number]
    other_lamps = set(lamps) - {current_lamp}
    canvas.itemconfig(current_lamp, fill=color)
    
    for lamp in other_lamps:
        canvas.itemconfig(lamp, fill='gray')


def update_lamp(
    generator: Generator[str],
    canvas: tk.Canvas,
    lamps: list[int],
) -> None:
    value = next(generator)
    
    if value == "red":
        enable_lamp(0, 'red', lamps, canvas)
        save_colour('red')
    elif value == "yellow":
        enable_lamp(1, 'yellow', lamps, canvas)
        save_colour(f'yellow|{read_color()}')
    elif value == "green":
        enable_lamp(2, 'green', lamps, canvas)
        save_colour('green')
    
    canvas.after(
        1000,
        update_lamp,
        generator,
        canvas,
        lamps,
    )


def main() -> None:
    root = tk.Tk()
    root.title("Лампочка")
    canvas = tk.Canvas(root, width=400, height=400, bg="white")
    canvas.pack()
    
    lamps = [
        canvas.create_oval(50, 50, 150, 150, fill="gray"),
        canvas.create_oval(50, 170, 150, 270, fill="gray"),
        canvas.create_oval(50, 290, 150, 390, fill="gray"),
    ]
    colors = read_color().split('|')
    
    initial_color = colors[0]
    trigger_color = None
    
    if len(colors) == 2:
        trigger_color = colors[1]
        
    print("INITIAL COLOR", initial_color, "TRIGGER COLOR", trigger_color)
    
    generator = colour_generator(
        initial_color,
        trigger_color
    )
    
    update_lamp(
        generator,
        canvas,
        lamps
    )
    
    root.mainloop()


main()
