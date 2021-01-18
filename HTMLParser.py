import sys
import pandas as pd
from html.parser import HTMLParser

# Constants used in parsing
COLUMN_CLASS = "ellipsis smart-caption__text"
COMPANY_NAME_PREFIX = "/profile/"
COLUMN_DATA_CLASS = "ellipsis"
CELL_PREFIX = "search-results-data-table-row"
CELL = "cell"
SPAN = "span"
CSV_FILE = "converted.csv"

# Global variables
is_col = False
is_company_name = False
is_column_data = False

split_col = 0
cell_loc = (-1, -1)

# Extracted Data
column_names = []
company_names = []
loc_to_data = {}


class CustomHTMLParser(HTMLParser):

    def handle_starttag(self, tag, attrs):
        global is_col
        global is_company_name
        global is_column_data
        global cell_loc
        for k, v in attrs:
            # Start tag for a column name
            if v == COLUMN_CLASS:
                is_col = True
            # Start tag for a company name
            elif v.startswith(COMPANY_NAME_PREFIX):
                is_company_name = True
            # Tag identifying a cell in the table - must include both row and column
            elif v.startswith(CELL_PREFIX) and CELL in v:
                tokens = v.split("-")
                cell_loc = int(tokens[5]), int(tokens[7]) # row, col
            # Start tag for data in the table
            elif v == COLUMN_DATA_CLASS:
                is_column_data = True

    # Some of the column headers are split into multiple elements/lines, so split_col detects that
    def handle_endtag(self, tag):
        global split_col
        if tag == SPAN:
            split_col += 1
        else:
            split_col = 0

    def handle_data(self, data):
        global is_company_name
        if is_col:
            self.add_column_name(data)
        elif is_company_name:
            company_names.append(data)
            is_company_name = False
        elif is_column_data:
            self.add_column_data(cell_loc, data)
        else:
            pass

    # Adds the primary identifer column "Column Name"
    def add_column_name(self, data):
        global is_col
        global column_names
        global split_col
        if split_col > 0:
            column_names[-1] = column_names[-1] + data
        else:
            column_names.append(data)
        is_col = False

    # Adds other columns in the table, as specified by location
    def add_column_data(self, loc, data):
        global is_column_data
        global loc_to_data
        loc_to_data[loc] = data
        is_column_data = False


if __name__ == "__main__":
    # Default to html.txt if no file specified
    filename = "html.txt"
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    print("Converting {0} to CSV...".format(filename))
    file = open(filename)
    parser = CustomHTMLParser()
    parser.feed(file.read())
    file.close()

    # Convert extracted data into lists of columns - done column-wise because the primary column is separated in HTML
    df_data_raw = [company_names]
    num_cols, num_rows = len(column_names), len(company_names)
    for c in range(num_cols - 1): # Account for the primary "Company Name" column, which isn't included here
        curr_col = [""] * num_rows
        for r in range(num_rows):
            if (r, c) in loc_to_data:
                curr_col[r] = loc_to_data[(r, c)]
        df_data_raw.append(curr_col)

    # Convert list of columns into dictionary to pass into data frame
    df_data_dict = {}
    for i, col in enumerate(df_data_raw):
        df_data_dict[column_names[i]] = col

    # Create dataframe and start index at 1 instead of 0 (default)
    df = pd.DataFrame(df_data_dict, index=range(1, num_rows+1))
    df_rows, df_cols = df.shape

    # Save as CSV
    df.to_csv(CSV_FILE)
    print("Successfully extracted {0} rows and {1} columns, saved to {2}!".format(df_rows, df_cols, CSV_FILE))

