import matplotlib.pyplot as plt

# Simple test plot to ensure window pops up
def test_plot():
    fig, ax = plt.subplots()
    ax.plot([0, 10], [0, 10], label="Diagonal Line")
    ax.legend()

    def on_click(event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            print(f"Clicked at X: {x:.3f}, Y: {y:.3f}")
            # Normally, you'd send x and y to your motor control logic here

    fig.canvas.mpl_connect('button_press_event', on_click)

    plt.show()

if __name__ == "__main__":
    test_plot()
