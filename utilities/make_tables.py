from sqlalchemy import MetaData, Table, Column, Integer, Boolean, Float
from sys import argv


# Create the tables
def create(engine):
    metadata_obj = MetaData()

    Table(
        'XBTZARcandles',
        metadata_obj,
        Column('Time', Integer, primary_key=True),
        Column('open', Float),
        Column('close', Float),
        Column('high', Float),
        Column('low', Float),
        Column('volume', Float),
        Column('change', Float),
        Column('tminus_1', Float),
        Column('vol_1', Float),
        Column('tminus_2', Float),
        Column('vol_2', Float),
        Column('tminus_3', Float),
        Column('vol_3', Float),
        Column('ema12', Float),
        Column('ema12_diff', Float),
        Column('signal', Boolean)
    )
    Table(
        'ETHZARcandles',
        metadata_obj,
        Column('Time', Integer, primary_key=True),
        Column('open', Float),
        Column('close', Float),
        Column('high', Float),
        Column('low', Float),
        Column('volume', Float),
        Column('change', Float),
        Column('tminus_1', Float),
        Column('vol_1', Float),
        Column('tminus_2', Float),
        Column('vol_2', Float),
        Column('tminus_3', Float),
        Column('vol_3', Float),
        Column('ema12', Float),
        Column('ema12_diff', Float),
        Column('signal', Boolean)
    )

    Table(
        'ETHZARderivatives',
        metadata_obj,
        Column('late_close', Integer, primary_key=True),
        Column('late_ema', Float),
        Column('max_high', Integer),
        Column('min_low', Float),
        Column('max_close', Float),
        Column('min_close', Float),
        Column('avg_close', Float)
    )
    Table(
        'XBTZARderivatives',
        metadata_obj,
        Column('late_close', Integer, primary_key=True),
        Column('late_ema', Float),
        Column('max_high', Integer),
        Column('min_low', Float),
        Column('max_close', Float),
        Column('min_close', Float),
        Column('avg_close', Float)
    )

    metadata_obj.create_all(engine)
