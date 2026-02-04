"""
Calculator endpoints for income tax and impact simulations
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class TaxCalculationRequest(BaseModel):
    """Tax calculation request"""
    income: float = Field(..., gt=0, description="Annual income in INR")
    regime: str = Field("new", description="Tax regime: 'new' or 'old'")
    deductions: float = Field(0, ge=0, description="Total deductions (80C, 80D, etc.)")


class TaxBreakdown(BaseModel):
    """Tax breakdown by slab"""
    slab_min: int
    slab_max: int | None
    rate: float
    taxable_amount: float
    tax_amount: float


class TaxCalculationResponse(BaseModel):
    """Tax calculation response"""
    gross_income: float
    deductions: float
    taxable_income: float
    tax_slabs: list[TaxBreakdown]
    total_tax: float
    cess: float  # 4% cess on tax
    total_liability: float
    effective_rate: float
    take_home: float


@router.post("/calculate-tax", response_model=TaxCalculationResponse)
async def calculate_income_tax(request: TaxCalculationRequest):
    """
    Calculate income tax based on new/old regime
    
    Returns detailed breakdown and effective tax rate
    """
    income = request.income
    deductions = request.deductions if request.regime == "old" else 0
    taxable_income = max(0, income - deductions)
    
    # Define slabs
    if request.regime == "new":
        slabs = [
            (0, 300000, 0),
            (300000, 600000, 0.05),
            (600000, 900000, 0.10),
            (900000, 1200000, 0.15),
            (1200000, 1500000, 0.20),
            (1500000, None, 0.30),
        ]
    else:
        slabs = [
            (0, 250000, 0),
            (250000, 500000, 0.05),
            (500000, 1000000, 0.20),
            (1000000, None, 0.30),
        ]
    
    # Calculate tax
    remaining = taxable_income
    total_tax = 0
    breakdown = []
    
    for slab_min, slab_max, rate in slabs:
        if remaining <= 0:
            break
        
        # Amount in this slab
        if slab_max is None:
            taxable_in_slab = remaining
        else:
            taxable_in_slab = min(remaining, slab_max - slab_min)
        
        tax_in_slab = taxable_in_slab * rate
        total_tax += tax_in_slab
        
        if taxable_in_slab > 0:
            breakdown.append(TaxBreakdown(
                slab_min=slab_min,
                slab_max=slab_max,
                rate=rate,
                taxable_amount=taxable_in_slab,
                tax_amount=tax_in_slab
            ))
        
        remaining -= taxable_in_slab
    
    # Add 4% cess
    cess = total_tax * 0.04
    total_liability = total_tax + cess
    effective_rate = (total_liability / income * 100) if income > 0 else 0
    take_home = income - total_liability
    
    return TaxCalculationResponse(
        gross_income=income,
        deductions=deductions,
        taxable_income=taxable_income,
        tax_slabs=breakdown,
        total_tax=total_tax,
        cess=cess,
        total_liability=total_liability,
        effective_rate=round(effective_rate, 2),
        take_home=take_home
    )


@router.post("/compare-regimes")
async def compare_tax_regimes(income: float, deductions: float = 0):
    """
    Compare tax liability between old and new regime
    """
    new_regime = await calculate_income_tax(
        TaxCalculationRequest(income=income, regime="new", deductions=0)
    )
    old_regime = await calculate_income_tax(
        TaxCalculationRequest(income=income, regime="old", deductions=deductions)
    )
    
    savings = old_regime.total_liability - new_regime.total_liability
    better_regime = "new" if savings > 0 else "old"
    
    return {
        "income": income,
        "deductions": deductions,
        "new_regime": new_regime,
        "old_regime": old_regime,
        "savings": abs(savings),
        "better_regime": better_regime,
        "recommendation": f"{'New' if better_regime == 'new' else 'Old'} regime saves ₹{abs(savings):,.0f}"
    }
