
from typing import Optional
from datetime import datetime
import sqlalchemy as sqla
from sqlalchemy import orm
from sqlalchemy.dialects import postgresql


__all__ = [
    'BaseModel',
    'NPSFileCode',
    'ParkDivisionCode',
    'ProgramAreaCode',
    'TransferLocationCode',
    'Collection',
    'Tag',
    'CollectionTag',
    'RecordTransferBox',
    'RecordTransferFolder',
    'Record',
    'DestructionRequest',
    'DestroyedCollection'
]

# class BaseModel(DeclarativeBase):
#     pass
BaseModel = orm.declarative_base()

class LookupTableMixin:
    """Mixin for lookup tables with all common columns"""

    id:         orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    name:       orm.Mapped[str] = sqla.Column(sqla.String(50))
    code:       orm.Mapped[int] = sqla.Column(sqla.Integer, unique=True)
    sort_order: orm.Mapped[Optional[int]] = sqla.Column(sqla.Integer, nullable=True)

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f'{class_name}(id={self.id!r}, code={self.code!r}, name={self.name!r}, sort_order={self.sort_order!r})'


class DataTableMixin:
    """Mixin for all data tables, so they'll all have created/modified meta fields"""
    id:                 orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    created_by:         orm.Mapped[str] = sqla.Column(sqla.String(50))
    create_time:        orm.Mapped[datetime] = sqla.Column(postgresql.TIMESTAMP)
    last_modified_by:   orm.Mapped[str] = sqla.Column(sqla.String(50))
    last_modified_time:     orm.Mapped[datetime] = sqla.Column(postgresql.TIMESTAMP)


# -------- Lookup tables ------------
class NPSFileCode(LookupTableMixin, BaseModel):
    __tablename__ = 'nps_file_codes'

    name:                   orm.Mapped[str] = sqla.Column(sqla.String(255))
    nps_item:               orm.Mapped[str] = sqla.Column(sqla.String(25))
    nps_authority:          orm.Mapped[str] = sqla.Column(sqla.String(50))
    drs_authority:          orm.Mapped[str] = sqla.Column(sqla.String(50))
    retention_years:        orm.Mapped[Optional[int]] = sqla.Column(sqla.Integer)
    retention_description:  orm.Mapped[str] = sqla.Column(sqla.String(50))

    def __repr__(self) -> str:
        return super().__repr__()[:-1] + f', nps_item={self.nps_item!r}, retention_years={self.retention_years!r})'


class ParkDivisionCode(LookupTableMixin, BaseModel):
    __tablename__ = 'park_division_codes'


class ProgramAreaCode(LookupTableMixin, BaseModel):
    __tablename__ = 'program_area_codes'

    park_division_code: orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('park_division_codes.code', onupdate='CASCADE', ondelete='RESTRICT')
    )


class TransferLocationCode(LookupTableMixin, BaseModel):
    __tablename__ = 'transfer_location_codes'



# -------- Data tables ------------
class Collection(DataTableMixin, BaseModel):
    __tablename__ = "collections"

    # columns
    collection_name:    orm.Mapped[str] = sqla.Column(sqla.String(255))
    original_location:  orm.Mapped[str] = sqla.Column(sqla.String(255))
    nps_file_code:      orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('nps_file_codes.code', onupdate='CASCADE', ondelete='RESTRICT')
    )
    description:        orm.Mapped[str] = sqla.Column(postgresql.TEXT)
    start_date:         orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    end_date:           orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    retention_date:     orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    source_file:        orm.Mapped[str] = sqla.Column(sqla.String(255), nullable=True)
    volume_cu_ft:       orm.Mapped[int] = sqla.Column(sqla.Integer, nullable=True)
    media_type:         orm.Mapped[str] = sqla.Column(sqla.String(50))
    program_area_code:  orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('program_area_codes.code', onupdate='CASCADE', ondelete='RESTRICT')
    )
    # record transfer columns
    transfer_location_code: orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('transfer_location_codes.code', onupdate='CASCADE', ondelete='RESTRICT')
    )
    prepared_by:            orm.Mapped[str] = sqla.Column(sqla.String(50), nullable=True)
    prepared_date:          orm.Mapped[datetime] = sqla.Column(postgresql.DATE, nullable=True)
    arcis_transfer_number:  orm.Mapped[str] = sqla.Column(sqla.String(50), nullable=True, unique=True)
    disposition_date:       orm.Mapped[datetime] = sqla.Column(postgresql.DATE, nullable=True)
    sf135_path:             orm.Mapped[str] = sqla.Column(sqla.String(255), nullable=True)
    box_inventory_path:     orm.Mapped[str] = sqla.Column(sqla.String(255), nullable=True)

    # ORM attributes
    tags: orm.Mapped[list['Tag']] = orm.relationship(
        'Tag', secondary='collection_tags', back_populates='collections'
    )
    records: orm.Mapped[list['Record']] = orm.relationship(
        'Record', back_populates='collection', cascade='all, delete-orphan'
    )
    destroyed_record: orm.Mapped[list['DestroyedCollection']] = orm.relationship(
        'DestroyedCollection', back_populates='collection', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'''Collection(id={self.id!r}, collection_name={self.collection_name!r})'''


class Tag(BaseModel):
    __tablename__ = 'tags'

    # columns
    id:         orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    tag_text:   orm.Mapped[str] = sqla.Column(sqla.String(50), unique=True)

    # ORM attributes
    collections: orm.Mapped[list['Collection']] = orm.relationship(
        'Collection', secondary='collection_tags', back_populates='tags'
    )

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r}, tag_text={self.tag_text!r})'


class CollectionTag(BaseModel):
    __tablename__ = 'collection_tags'

    id:             orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    collection_id:  orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('collections.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    tag_id:         orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('tags.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    def __repr__(self) -> str:
        return f'CollectionTag(id={self.id!r}, collection_id={self.collection_id!r}, tag_id={self.tag_id!r})'


class RecordTransferBox(BaseModel):
    __tablename__ = 'record_transfer_boxes'

    id:         orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    box_number: orm.Mapped[int] = sqla.Column(sqla.Integer)
    collection_id: orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('collections.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    def __repr__(self) -> str:
        return f'Tag(id={self.id!r})'


class RecordTransferFolder(BaseModel):
    __tablename__ = 'record_transfer_folders'

    id:            orm.Mapped[int] = sqla.Column(sqla.Integer, primary_key=True)
    folder_number: orm.Mapped[int] = sqla.Column(sqla.Integer)
    box_id:        orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('record_transfer_boxes.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    # ORM attributes
    records: orm.Mapped[list['Record']] = orm.relationship(
        'Record', back_populates='folder', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'RecordTransferFolder(id={self.id!r},box_id={self.box_id!r}, folder_number={self.folder_number!r})'


class Record(DataTableMixin, BaseModel):
    __tablename__ = 'records'

    collection_id:  orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('collections.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    # This structure requires that records are related to boxes via folders. If no folder is given in box inventory,
    #   folder has to be filled in by default with folder_number = 1
    folder_id:      orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('record_transfer_folders.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    file_title:     orm.Mapped[str] = sqla.Column(sqla.String(255))
    start_date:     orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    end_date:       orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    cutoff_date:    orm.Mapped[datetime] = sqla.Column(postgresql.DATE)
    description:    orm.Mapped[str] = sqla.Column(postgresql.TEXT)

    # ORM attributes
    collection: orm.Mapped['Collection'] = orm.relationship(
        'Collection', back_populates='records'
    )
    folder: orm.Mapped['RecordTransferFolder'] = orm.relationship(
        'RecordTransferFolder', back_populates='records'
    )

    def __repr__(self) -> str:
        return f'Record(id={self.id!r}, collection_id={self.collection_id!r}, file_title={self.file_title!r})'


class DestructionRequest(DataTableMixin, BaseModel):

    __tablename__ = 'destruction_requests'

    office_name:        orm.Mapped[str] = sqla.Column(sqla.String(255), default='Denali National Park and Preserve')
    requestor_name:     orm.Mapped[str] = sqla.Column(sqla.String(50))
    requestor_phone:    orm.Mapped[str] = sqla.Column(sqla.String(50))
    requestor_email:    orm.Mapped[str] = sqla.Column(sqla.String(50))
    source_file:        orm.Mapped[str] = sqla.Column(sqla.String(255))

    # ORM attributes
    destroyed_collections: orm.Mapped[list['DestroyedCollection']] = orm.relationship(
        'DestroyedCollection', back_populates='destruction_request', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'DestructionRequest(id={self.id!r})'


class DestroyedCollection(DataTableMixin, BaseModel):

    __tablename__ = 'destroyed_collections'

    destruction_request_id: orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('destruction_requests.id', onupdate='CASCADE', ondelete='CASCADE')
    )
    collection_id: orm.Mapped[int] = sqla.Column(
        sqla.Integer,
        sqla.ForeignKey('collections.id', onupdate='CASCADE', ondelete='CASCADE')
    )

    # ORM attributes
    destruction_request: orm.Mapped['DestroyedCollection'] = orm.relationship(
        'DestructionRequest', back_populates='destroyed_collections'
    )
    collection: orm.Mapped['Collection'] = orm.relationship(
        'Collection', back_populates='destroyed_record'
    )

    def __repr__(self) -> str:
        return f'DestructionRequest(id={self.id!r}, destruction_request_id={self.destruction_request_id!r}, collection_id={self.collection_id!r})'
