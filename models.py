from sqlalchemy import Column, Integer, String, Float, CheckConstraint
from pydantic import BaseModel
from typing import Optional
from database import Base



class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        String,
        nullable=False,        
        unique=True,           
        index=True           
    )

    customer = Column(
        String,
        nullable=False,       
        index=True            
    )

    amount = Column(Float, nullable=False)
    date = Column(String, nullable=False)


    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
    )



class InvoiceResponse(BaseModel):
    id: int
    order_id: str
    customer: str
    amount: float
    date: str

    class Config:
        from_attributes = True   


class InvoiceData(BaseModel):
    order_id: str
    customer: str
    amount: float
    date: str