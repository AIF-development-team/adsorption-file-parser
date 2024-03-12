import xml.etree.ElementTree as ET

tree = ET.parse('tests/data/problems/ASAP-001-324.XML')
root = tree.getroot()
# Extract information from the XML tree
titles = root.findall(".//title")
for title in titles:
    print("Title:", title.text)

started_time = root.find(".//header/table/tablecolumn[@column='1']/string[1]")
print("Started:", started_time.text)

completed = root.find(".//tablecolumn[@column='1']/string[2]")
report_time = root.find(".//tablecolumn[@column='1']/string[3]")
sample_mass = root.find(".//tablecolumn[@column='1']/string[4]")

# print("Started:", started.text)
print("Completed:", completed.text)
print("Report Time:", report_time.text)
print("sample mass:", sample_mass.text)

# Extracting curve data from the graph
curve_data = root.findall(".//curve/curvedata[@axistitle='Absolute Pressure (mbar)']")
for data in curve_data:
    numbers = data.findall("number")
    pressure_values = [float(number.text) for number in numbers]
    print("Pressure Values:", pressure_values)
