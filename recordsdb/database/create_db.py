"""
Create database objects and fill in lookup tables.

required params:
    retention_schedule_csv: A .csv file of the latest NPS/DOI retention schedule definitions. Required fields include:
            name -          text description of the retention schedule
            nps_item -      NPS file code (e.g., 1.A.1)
            nps_authority - NPS retention schedule citation
            drs_authority - DOI Retention Schedule citation
            retention_description - length of retention (e.g., 10 years, permanent)
"""

import sys
import pandas as pd

import models
from git.recordsdb.database import engine


def main(retention_schedule_csv: str) -> None:

    # Emit create database DDLs
    models.BaseModel.metadata.create_all(engine)

    # Add data to lookup tables
    # nps_file_codes
    retention_schedules = pd.read_csv(retention_schedule_csv).dropna(how='any')
    retention_schedules['code'] = retention_schedules.index + 1 # codes start at 1, not 0
    retention_schedules['sort_order'] = retention_schedules.code
    retention_schedules['retention_years'] = retention_schedules.retention_description.str.extract('(\d+)')

    # Remove all leading and trailing spaces from str columns
    for column in retention_schedules.columns[retention_schedules.dtypes == object]:
        retention_schedules[column] = retention_schedules[column].str.strip()

    retention_schedules.to_sql('nps_file_codes', engine, if_exists='append', index=False)

    # park_division_codes
    division_str = '''
        Administration	Admin
        External Affairs	ExternalAffairs
        Facilities	Maint
        Interpretation and Education	Interp
        Resources	ResMgmt
        Superintendent's Office	Superintendent
        Visitor and Resource Protection	VRP
    '''
    divisions = pd.DataFrame(
        [s.strip().split('\t') for s in division_str.strip().split('\n')],
        columns=['name', 'short_name']
    )
    divisions['code'] = divisions.index + 1
    divisions['sort_order'] = divisions.code
    divisions.drop('short_name', axis=1)\
        .to_sql('park_division_codes', engine, index=False, if_exists='append')

    # program_area_codes
    program_str = '''
        Admin	Budget
        Admin	Human Resources
        Admin	IT
        Admin	Misc. Business Services
        Admin	Volunteer Program
        ExternalAffairs	Commercial Services
        ExternalAffairs	Planning
        Maint	Auto Shop
        Maint	Buildings & Utilities
        Maint	Roads and Trails
        Maint	Special Projects
        Interp	Interpretive Services
        Interp	K-12 Education
        Interp	Media Products
        Interp	MSLC
        ResMgmt	Cultural Resources
        ResMgmt	Fire
        ResMgmt	Natural Resources
        ResMgmt	Pysical Resources
        VRP	Backcountry
        VRP	Comm. Center
        VRP	General Rangers
        VRP	Kennels
        VRP	Law Enforcement
        VRP	Mountain Operations
        Superintendent	Admin Record
        Superintendent	Public Affairs
        Superintendent	Safety
    '''
    programs = pd.DataFrame(
        [s.strip().split('\t') for s in program_str.strip().split('\n')],
        columns=['division_short_name', 'name']
    )
    programs['park_division_code'] = \
        programs.merge(divisions, left_on='division_short_name', right_on='short_name').code
    programs['code'] = divisions.index + 1
    programs['sort_order'] = divisions.code
    programs.drop('division_short_name', axis=1)\
        .to_sql('program_area_codes', engine, index=False, if_exists='append')

    # transfer_location_codes
    transfer_locations = pd.DataFrame(
        {'name': ['Federal Records Center', 'National Archives and Records Administration', 'Other']}
    )
    transfer_locations['code'] = transfer_locations.index + 1
    transfer_locations['sort_order'] = transfer_locations.code
    transfer_locations.to_sql('transfer_location_codes', engine, index=False, if_exists='append')


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
