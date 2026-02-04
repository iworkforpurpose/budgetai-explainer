"""
Data endpoints for visualizations
Returns structured data for tax slabs, allocations, etc.
"""
from fastapi import APIRouter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class TaxSlab(BaseModel):
    """Tax slab model"""
    min_income: int
    max_income: int | None
    rate: float
    description: str


class AllocationItem(BaseModel):
    """Budget allocation item"""
    sector: str
    amount: float  # in crores
    percentage: float


class TaxSlabsResponse(BaseModel):
    """Tax slabs response"""
    year: str
    regime: str
    slabs: List[TaxSlab]


class AllocationsResponse(BaseModel):
    """Budget allocations response"""
    year: str
    total: float
    allocations: List[AllocationItem]


@router.get("/tax-slabs", response_model=TaxSlabsResponse)
async def get_tax_slabs(regime: str = "new"):
    """
    Get income tax slabs for FY 2026-27
    
    Query params:
        regime: 'new' or 'old'
    """
    if regime == "new":
        slabs = [
            TaxSlab(min_income=0, max_income=300000, rate=0, description="No tax"),
            TaxSlab(min_income=300000, max_income=600000, rate=5, description="5%"),
            TaxSlab(min_income=600000, max_income=900000, rate=10, description="10%"),
            TaxSlab(min_income=900000, max_income=1200000, rate=15, description="15%"),
            TaxSlab(min_income=1200000, max_income=1500000, rate=20, description="20%"),
            TaxSlab(min_income=1500000, max_income=None, rate=30, description="30%"),
        ]
    else:  # old regime
        slabs = [
            TaxSlab(min_income=0, max_income=250000, rate=0, description="No tax"),
            TaxSlab(min_income=250000, max_income=500000, rate=5, description="5%"),
            TaxSlab(min_income=500000, max_income=1000000, rate=20, description="20%"),
            TaxSlab(min_income=1000000, max_income=None, rate=30, description="30%"),
        ]
    
    return TaxSlabsResponse(
        year="2026-27",
        regime=regime,
        slabs=slabs
    )


@router.get("/allocations", response_model=AllocationsResponse)
async def get_budget_allocations():
    """
    Get major budget allocations by sector for 2026-27
    
    Based on Budget at a Glance
    """
    # Approximate values from budget documents (in crores)
    allocations = [
        AllocationItem(sector="Defence", amount=650000, percentage=12.5),
        AllocationItem(sector="Education", amount=450000, percentage=8.5),
        AllocationItem(sector="Healthcare", amount=380000, percentage=7.2),
        AllocationItem(sector="Infrastructure", amount=1100000, percentage=21.0),
        AllocationItem(sector="Agriculture", amount=320000, percentage=6.1),
        AllocationItem(sector="Social Welfare", amount=580000, percentage=11.2),
        AllocationItem(sector="Energy", amount=280000, percentage=5.4),
        AllocationItem(sector="Other", amount=1440000, percentage=28.1),
    ]
    
    total = sum(item.amount for item in allocations)
    
    return AllocationsResponse(
        year="2026-27",
        total=total,
        allocations=allocations
    )
