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
footer_text = [
    "Press (", ("green", "B")," -> Buckets) ",
    "(", ("green", "S")," -> SQS) ",
    "(", ("green", "G")," -> SG) ",
    "(", ("red", "Q")," -> Quit)",
]
menu = urwid.Text(footer_text)

# Create the text widget to display results
result_text = urwid.Text("Select datasource to fetch")
result_filler = urwid.Filler(result_text, valign="top", top=1, bottom=1)
v_padding = urwid.Padding(result_filler, left=1, right=1)
result_table = urwid.LineBox(v_padding)


# Create the text widget to display results
detail_text = urwid.Text("Fetching account summary")
detail_filler = urwid.Filler(detail_text, valign="top", top=1, bottom=1)
v_padding = urwid.Padding(detail_filler, left=1, right=1)
detail_table = urwid.LineBox(v_padding)

# Arrange the widgets within the Frame
columns = urwid.Columns(
    [
        ("weight", 40, detail_table),
        ("weight", 60, result_table),
    ]
)
grid = urwid.Frame(header=header, body=columns, footer=menu)


###############################################################################
#  2.  Create Function to fetch results on changing the data source
###############################################################################


def get_aws_buckets_client():
    # list of buckets present in AWS using S3 client
    session = boto3.session.Session()
    s3_client = session.client("s3")

    response = s3_client.list_buckets()
    buckets = []
    for bucket in response["Buckets"]:
        buckets.append([bucket["Name"], ""])

    return buckets


def get_aws_sqs():

    # get list of SQS queues with Message count

    results = []
    sqs = boto3.client("sqs")
    queues = sqs.list_queues()
    for q in queues["QueueUrls"]:
        queue_attributes = sqs.get_queue_attributes(QueueUrl=q, AttributeNames=["All"])
        message_count = queue_attributes["Attributes"]["ApproximateNumberOfMessages"]
        results.append([q.split("/")[-1], message_count])
    return results


def get_aws_sg():

    # get list of security groups
    client = boto3.client("ec2")
    sg = client.describe_security_groups()

    return [["SG", k["GroupName"]] for k in sg["SecurityGroups"]]


def get_acc_summary():
    sts = boto3.client("sts")
    my_session = boto3.session.Session()
    my_region = my_session.region_name
    caller = sts.get_caller_identity()
    return [
        {"Region": my_region}, caller
    ]


def fetch_results():

    results = [
        ("headers", "Item ".ljust(50, " ")),
        ("headers", "Detail".ljust(50, " ")),
    ]
    if source == "S3":
        data = get_aws_buckets_client()
    elif source == "SQS":
        data = get_aws_sqs()
    elif source == "SG":
        data = get_aws_sg()

    for item in data:
        txt = f"\n{item[0].ljust(50, ' ')}{item[1].ljust(50, ' ')}"
        results.append(("text", txt))
    return {"list": results, "details": results}


def fetch_initial_data():
    info_panel = [
        ("headers", "Account Info:\n "),
    ]
    for item in get_acc_summary():
        info_panel.append(("footer", f"{json.dumps(item, indent=4)} \n"))
    return info_panel


source = "s3"  # stores the currently active data source

###############################################################################
#  3.  Handle key presses to change data source or to exit the app
###############################################################################


def handle_input_events(key):
    global source

    if key in ["B", "b"]:
        source = "S3"
        redraw_ui(main_loop, "")

    elif key in ["S", "s"]:
        source = "SQS"
        redraw_ui(main_loop, "")

    elif key in ["G", "g"]:
        source = "SG"
        redraw_ui(main_loop, "")

    elif key in ["Q", "q"]:
        raise urwid.ExitMainLoop()


###############################################################################
#  4.  Function to redraw ui with results from the currently active data source
###############################################################################
def update_initial_data(_loop, _data):

    global detail_table  # todo remove global
    detail_table.base_widget.set_text(fetch_initial_data())


def redraw_ui(_loop, _data):
    """
    Redraw the ui with latest results from the currently selected data source
    """
    menu.base_widget.set_text(
        list(tuple(footer_text + [("red", f" Loading {source}....")]))
    )
    result_table.base_widget.set_text(("red", f" Loading {source}...."))
    main_loop.draw_screen()
    results = fetch_results()
    result_table.base_widget.set_text(results["list"])
    menu.base_widget.set_text(
        list(tuple(footer_text + [("green", f" {source} Loaded!")]))
    )


##############################################################################
#  5.  Lets run the app now!
##############################################################################

main_loop = urwid.MainLoop(grid, palette, unhandled_input=handle_input_events)
main_loop.set_alarm_in(1, update_initial_data)
main_loop.run()
