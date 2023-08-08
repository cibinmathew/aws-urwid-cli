import urwid


def handle_input_events(key):

    # On pressing q, lets exit our app
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()

    # On pressing any other key, echo it to the screen
    txt.set_text(f"You have pressed {repr(key)}")


# Lets create a basic Text widget using Text class
txt = urwid.Text("Hello World")
fill = urwid.Filler(txt, "top")

# Mainloop handles the input events
loop = urwid.MainLoop(fill, unhandled_input=handle_input_events)

loop.run()  # This starts the mainloop
