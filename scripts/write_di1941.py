"""
Read a destruction request log Excel doc and fill a DI-1941 form from the data.
Destruction log template: P:\Records Management\Temporary Records\destruction_log_dena_template.xlsx
DI-1949: P:\Records Management\Temporary Records\Documentation-of-Temporary-Records-Destruction--DI-1941-BLANK.pdf
"""
import os
import sys
import re
import math
import openpyxl
import PyPDF2
import pandas as pd

PDF_ROW_COUNT = 15
TEMPLATE_PDF_PATH = r"\\inpdenafiles02\parkwide\Records Management\Temporary Records\Documentation-of-Temporary-Records-Destruction--DI-1941-BLANK.pdf"


def write_di1941(excel_path, output_path):

    reader = PyPDF2.PdfReader(TEMPLATE_PDF_PATH)
    fields = reader.get_fields()
    first_page = reader.pages[0]

    #excel_doc = pd.ExcelFile(excel_path)
    # Get header info
    workbook = openpyxl.load_workbook(filename=excel_path, data_only=True)
    worksheet = workbook['Entry Log']
    header_info = {
        '2 OfficeRow1': worksheet['A5'].value,
        '3 DivisionBranchSectionRow1': worksheet['A7'].value,
        'Requestor NameRow1': worksheet['B5'].value,
        '4a Requestor PhoneRow1': worksheet['C5'].value,
        '4b Requestor eMailRow1': worksheet['F5'].value,
        '5 ManagerSupervisor NameRow1': worksheet['B7'].value,
        '5a MgrSupv PhoneRow1': worksheet['C7'].value,
        '5b MgrSupv eMailRow1': worksheet['F7'].value
    }

    entry_log = pd.read_excel(workbook, sheet_name='Entry Log', usecols='A:I', engine='openpyxl', skiprows=7)\
        .dropna(subset=['File Code', 'Records Series Name/Description'], how='any')
    file_codes = pd.read_excel(workbook, sheet_name='NPS-DRS Crosswalk', engine='openpyxl').dropna()
    entry_log['date_range'] = \
        entry_log['Start Date (mm/yyyy)'].dt.strftime('%m/%Y') + ' - ' +\
        entry_log['End Date (mm/yyyy)'].dt.strftime('%m/%Y')
    # only use DRS where not "proposed"
    merged = pd.merge(entry_log, file_codes, how='left', on='File Code')
    drs_is_proposed = merged['Corresponding DRS Authority'].str.contains('proposed')
    entry_log['file_code'] = merged.loc[merged['Corresponding DRS Authority'].isna(), 'File Code']
    entry_log.loc[entry_log.file_code.isna(), 'file_code'] = merged['NPS Authority'].where(drs_is_proposed, merged['Corresponding DRS Authority']).loc[~merged['Corresponding DRS Authority'].isna()]
    entry_log['volume'] = entry_log['Volume (ft3)'].astype(str) + ' ft, paper'
    entry_log['disposal_date'] = entry_log['Retention Date (mm/yyyy)'].dt.strftime('%m/%Y')
    field_names = list(fields.keys())


    # Each field in the DI-1941 table has a unique field name starting with a letter (a-g) corresponding to the column index and a number at the end corresponding to a row index. First make a list of the field names by searching all field names via regular expression. Zip that list with a list of field values and add it to the log_data dictionary. Since the table in the DI1941 only has 15 rows, loop through the entry log in blocks of 15 and write a new PDF for each block
    n_rows = len(entry_log)
    chunk_row_indices = range(PDF_ROW_COUNT, math.ceil(n_rows/PDF_ROW_COUNT) * PDF_ROW_COUNT + 1, PDF_ROW_COUNT)
    for pdf_index, chunk_row_index in enumerate(chunk_row_indices):
        log_entry_rows = entry_log.loc[chunk_row_index - PDF_ROW_COUNT : min(chunk_row_index - 1, n_rows)]
        log_data = {}
        #import pdb; pdb.set_trace()
        for row_index, row in log_entry_rows.iterrows():
            pdf_fields = []
            for i in range(7):
                regex = f'^{chr(i + 97)} .*Row{(row_index % PDF_ROW_COUNT) + 1}$' #97-102 are ASCII codes for a-g
                matches = list(filter(lambda x: re.match(regex, x), field_names))
                if not len(matches):
                    raise RuntimeError(f'No field name match found with regex {regex}')
                pdf_fields.extend(matches)
            log_data |= dict(
                zip(
                    pdf_fields,
                    row.loc[['file_code', 'Records Series Name/Description',  'date_range', 'disposal_date', 'Original Location', 'volume', 'Destruction Method']]
                        .tolist()
                )
            )

        # For some stupid reason, PyPDF2 maintains a reference to pages added to a writer, including the values of
        #   fields set with update_page_form_field_values. So re-read in the template PDF
        reader = PyPDF2.PdfReader(TEMPLATE_PDF_PATH)

        writer = PyPDF2.PdfWriter()
        writer.add_page(reader.pages[0])
        writer.update_page_form_field_values(writer.pages[0], header_info)

        writer.add_page(reader.pages[1])
        writer.update_page_form_field_values(writer.pages[-1], log_data)

        pdf_output_path = output_path if n_rows <= PDF_ROW_COUNT else re.sub('\.pdf$', f'_{pdf_index + 1}.pdf', output_path)
        with open(pdf_output_path, 'wb') as f:
            writer.write(f)

        # The reference to the reader has to be completely deleted from memory or the values of filled fields will
        #   persist, despite calling update_page_form_field_values again
        del reader

if __name__ == '__main__':
    write_di1941(*sys.argv[1:])