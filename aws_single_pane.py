import json

import boto3
import urwid

###############################################################################
#  1.  Set up the widgets (color scheme, a title, a table, a footer)
###############################################################################

# Set up a color scheme
palette = [
    ("titlebar", "dark magenta,bold", ""),
    ("headers", "dark magenta,bold", ""),
    ("green", "dark green,bold", ""),
    ("red", "dark red", ""),
    ("text", "dark magenta", ""),
]

titlebar = urwid.Text(("titlebar", " AWS Explorer"), align="center")
header = urwid.AttrMap(titlebar, "titlebar")

# Footer text
menu = urwid.Text(
    [
        " press (",("green", "S")," -> SQS) ",
        "(",("green", "B")," -> S3 Buckets) ",
        "(",("red", "Q")," -> Quit)",
    ]
)

# Create the text widget to display results
result_text = urwid.Text("Select datasource to fetch")
result_filler = urwid.Filler(result_text, valign="top", top=1, bottom=1)
v_padding = urwid.Padding(result_filler, left=1, right=1)
result_table = urwid.LineBox(v_padding)

# Arrange the widgets within the Frame
grid = urwid.Frame(header=header, body=result_table, footer=menu)


###############################################################################
#  2.  Create Function to fetch results on changing the data source
###############################################################################


# list of buckets present in AWS using S3 client
def get_aws_buckets_client():
    session = boto3.session.Session()
    s3_client = session.client("s3")
    response = s3_client.list_buckets()
    buckets = []
    for bucket in response["Buckets"]:
        buckets.append([bucket["Name"], ""])

    return buckets


# get list of SQS queues with Message count
def get_aws_sqs():

    results = []
    sqs = boto3.client("sqs")
    queues = sqs.list_queues()
    for q in queues["QueueUrls"]:
        queue_attributes = sqs.get_queue_attributes(QueueUrl=q, AttributeNames=["All"])
        message_count = queue_attributes["Attributes"]["ApproximateNumberOfMessages"]
        results.append([q.split("/")[-1], message_count])
    return results


def fetch_results():

    results = [
        ("headers", "Item ".ljust(70, " ")),
        ("headers", "Detail".ljust(50, " ")),
    ]

    if source == "s3":
        data = get_aws_buckets_client()
    elif source == "sqs":
        data = get_aws_sqs()

    for item in data:
        txt = f"\n{item[0].ljust(70, ' ')}{item[1].ljust(50, ' ')}"
        results.append(("text", txt))

    return results


source = "s3"  # stores the currently active data source

###############################################################################
#  3.  Handle key presses to change data source or to exit the app
###############################################################################


def handle_input_events(key):
    global source
    if key in ["B", "b"]:
        source = "s3"
        redraw_ui(main_loop, "")

    elif key in ["S", "s"]:
        source = "sqs"
        redraw_ui(main_loop, "")

    elif key in ["Q", "q"]:
        raise urwid.ExitMainLoop()


###############################################################################
#  4.  Function to redraw ui with results from the currently active data source
###############################################################################


def redraw_ui(_loop, _data):
    """
    Redraw the ui with latest results from the currently selected data source
    """

    main_loop.draw_screen()
    result_table.base_widget.set_text(fetch_results())


##############################################################################
#  5.  Lets run the app now!
##############################################################################

main_loop = urwid.MainLoop(grid, palette, unhandled_input=handle_input_events)
main_loop.run()
