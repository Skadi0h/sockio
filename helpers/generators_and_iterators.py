import tkinter as tk
from collections.abc import Generator
def main():
    value = ""
    with open('workfile', mode = "r", encoding="utf-8") as f:
        value = f.read()

    def plus_minus_calculator(colour: str | None = None) -> Generator[str]:
       while True:
            yield colour or "red"
            colour = ""
            yield "gray"
            yield "yellow"
            yield "gray"
            yield "green"
            yield "gray"
            yield "yellow"
            yield "gray"

    generator = plus_minus_calculator(value)
    root = tk.Tk()
    root.title("Лампочка")
    canvas = tk.Canvas(root, width=400, height=400, bg="white")
    canvas.pack()
    lamp1 = canvas.create_oval(50, 50, 150, 150, fill="gray")
    lamp2 = canvas.create_oval(50, 170, 150, 270, fill="gray")
    lamp3 = canvas.create_oval(50, 290, 150, 390, fill="gray")

    def update_lamp():
        nonlocal value, generator
        value = next(generator)
        if value == "red":
            canvas.itemconfig(lamp1, fill="red")
        elif value == "yellow":
            canvas.itemconfig(lamp2, fill="yellow")
        elif value == "green":
            canvas.itemconfig(lamp3, fill="green")
        else:
            canvas.itemconfig(lamp1, fill="gray")
            canvas.itemconfig(lamp2, fill="gray")
            canvas.itemconfig(lamp3, fill="gray")
        root.after(1000, update_lamp)

        f = open('workfile', 'w', encoding="utf-8")
        f.write(value)
        f.close()
    update_lamp()
    root.mainloop()
main()

