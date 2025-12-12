from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from datetime import date, datetime, timedelta
from typing import List
from app.database import get_db
from app.models.measurement import Measurement
from app.models.reports import CowWeightReport, DailyMilkReport, MilkSummaryReport, MeasurementDetail
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/milk/daily/{cow_id}/{report_date}", response_model=DailyMilkReport)
async def get_daily_milk_report_by_date(cow_id: str, report_date: date):
    """
    Get milk production report for a specific date.
    Returns total milk in liters and detailed measurements for that day.
    """
    try:
        db = get_db()
        
        with db.get_session() as session:
            # Get the start and end of the day
            start_datetime = datetime.combine(report_date, datetime.min.time())
            end_datetime = datetime.combine(report_date, datetime.max.time())
            
            # Query measurements for the specific date where unit is 'L'
            query = (
                select(Measurement)
                .where(
                    Measurement.unit == 'L',
                    Measurement.cow_id == cow_id,
                    Measurement.measured_at >= start_datetime,
                    Measurement.measured_at <= end_datetime
                )
                .order_by(Measurement.measured_at.desc()) # type: ignore
            )
            
            measurements = session.exec(query).all()
            
            if not measurements:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No milk measurements found for {report_date}"
                )
            
            # Calculate total
            total_liters = sum(m.value for m in measurements)
            
            result = DailyMilkReport(
                date=report_date,
                total_liters=round(total_liters, 2),
                measurement_count=len(measurements),
                measurements=[
                    MeasurementDetail(
                        cow_id=m.cow_id,
                        cow_name=m.name or "Unknown",
                        value=m.value,
                        measured_at=m.measured_at,
                        sensor_id=m.sensor_id
                    )
                    for m in measurements
                ]
            )
            
            logger.info(f"Retrieved {len(measurements)} measurements for {report_date}")
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting milk report for {report_date}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@router.get("/milk/summary/{cow_id}", response_model=MilkSummaryReport)
async def get_milk_summary(cow_id: str):
    """
    Get overall milk production summary.
    Returns total milk production and statistics.
    """
    try:
        db = get_db()
        
        with db.get_session() as session:
            # Get overall statistics
            query = (
                select(
                    func.sum(Measurement.value).label('total_liters'),
                    func.count(Measurement.id).label('total_measurements'), # type: ignore
                    func.avg(Measurement.value).label('avg_per_measurement'),
                    func.min(Measurement.measured_at).label('first_measurement'),
                    func.max(Measurement.measured_at).label('last_measurement')
                )
                .where(
                    Measurement.unit == 'L',
                    Measurement.cow_id == cow_id
                    )
            )
            
            result = session.exec(query).first()
            
            if not result or result[0] is None:
                return MilkSummaryReport(
                    total_liters=0,
                    total_measurements=0,
                    avg_per_measurement=0,
                    first_measurement=None,
                    last_measurement=None
                )
            
            summary = MilkSummaryReport(
                total_liters=round(float(result[0]), 2) if result[0] else 0,
                total_measurements=int(result[1]) if result[1] else 0,
                avg_per_measurement=round(float(result[2]), 2) if result[2] else 0,
                first_measurement=result[3],
                last_measurement=result[4]
            )
            
            logger.info("Generated milk production summary")
            return summary
            
    except Exception as e:
        logger.error(f"Error generating milk summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.get("/weight/{cow_id}", response_model=CowWeightReport)
async def get_cow_weight_report(cow_id: str):
    """
    Get weight report for a specific cow.
    Returns the current weight (most recent) and 30-day average.
    """
    try:
        db = get_db()
        
        with db.get_session() as session:
            # Get the most recent weight measurement
            current_query = (
                select(Measurement)
                .where(
                    Measurement.unit == 'kg',
                    Measurement.cow_id == cow_id
                )
                .order_by(Measurement.measured_at.desc()) # type: ignore
                .limit(1)
            )
            
            current_measurement = session.exec(current_query).first()
            
            if not current_measurement:
                raise HTTPException(
                    status_code=404,
                    detail=f"No weight measurements found for cow {cow_id}"
                )
            
            # Get measurements from the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            avg_query = (
                select(
                    func.avg(Measurement.value).label('avg_weight'),
                    func.count(Measurement.id).label('count') # type: ignore
                )
                .where(
                    Measurement.unit == 'kg',
                    Measurement.cow_id == cow_id,
                    Measurement.measured_at >= thirty_days_ago
                )
            )
            
            avg_result = session.exec(avg_query).first()
            
            avg_weight = None
            measurements_count = 0
            
            if avg_result and avg_result[0] is not None:
                avg_weight = round(float(avg_result[0]), 2)
                measurements_count = int(avg_result[1]) if avg_result[1] else 0
            
            # Check if the cow is ill
            ill = False
            dif_weight = current_measurement.value - avg_weight if avg_weight is not None else 0
            if avg_weight and dif_weight < -0.05 * avg_weight:
                ill = True

            report = CowWeightReport(
                cow_id=cow_id,
                cow_name=current_measurement.name or "Unknown",
                current_weight=round(current_measurement.value, 2),
                current_weight_date=current_measurement.measured_at,
                avg_weight_30_days=avg_weight,
                measurements_30_days=measurements_count,
                ill=ill
            )
            
            logger.info(f"Generated weight report for cow {cow_id}")
            return report
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weight report for cow {cow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating weight report: {str(e)}")
