"""
Gaṇita - Sanskrit Mathematics Engine
=====================================

Complete implementation of Sanskrit mathematical systems.

Includes:
- Śulba Sūtra geometry
- Āryabhaṭa system
- Brahmagupta system
- Vedic mathematics

*Visionary RM (Raj Mitra)* ⚡
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import math


@dataclass
class GeometricConstruction:
    """Represents a Śulba Sūtra geometric construction"""
    name: str
    sanskrit_name: str
    purpose: str
    steps: List[str]
    sūtra_reference: str


class SulbaGeometry:
    """
    Śulba Sūtra geometry (शुल्बसूत्र ज्यामिति).
    
    Ancient Indian geometry for altar construction.
    
    Key principles:
    - Pythagorean theorem (Baudhāyana sūtra)
    - Square root calculations
    - Area transformations
    - Altar constructions
    """
    
    def __init__(self):
        self.constructions = {
            "square_from_two": GeometricConstruction(
                name="Square from two squares",
                sanskrit_name="द्विचतुरस्र",
                purpose="Combine two equal squares into one",
                steps=[
                    "Take two equal squares",
                    "Place them diagonally",
                    "The diagonal forms the side of new square",
                ],
                sūtra_reference="Baudhāyana Śulba Sūtra 1.1",
            ),
            "circle_square": GeometricConstruction(
                name="Circle to square approximation",
                sanskrit_name="वृत्तचतुरस्र",
                purpose="Construct square approximately equal to circle",
                steps=[
                    "Take diameter d",
                    "Side of square = (7/8)d + (1/8)(d/7)",
                ],
                sūtra_reference="Baudhāyana Śulba Sūtra 2.9",
            ),
            "pythagorean": GeometricConstruction(
                name="Pythagorean theorem",
                sanskrit_name="कर्णचतुरस्र",
                purpose="Square on diagonal equals sum of squares on sides",
                steps=[
                    "Rectangle with sides a, b",
                    "Diagonal c satisfies: c² = a² + b²",
                ],
                sūtra_reference="Baudhāyana Śulba Sūtra 1.12",
            ),
        }
        
        # Pythagorean triples known to Śulba
        self.pythagorean_triples = [
            (3, 4, 5),
            (5, 12, 13),
            (8, 15, 17),
            (12, 35, 37),
            (15, 8, 17),
        ]
    
    def get_construction(self, name: str) -> Optional[GeometricConstruction]:
        """Get a specific construction"""
        return self.constructions.get(name)
    
    def calculate_square_root(self, n: float) -> float:
        """
        Calculate square root using Śulba method.
        
        Approximation: √n ≈ a + (n-a²)/(2a) where a = floor(√n)
        """
        a = int(math.sqrt(n))
        remainder = n - a*a
        approximation = a + remainder / (2*a)
        return approximation
    
    def transform_area(self, shape1: str, shape2: str, 
                       dimensions: Dict) -> Dict:
        """
        Transform area from one shape to another.
        
        Śulba methods for area-preserving transformations.
        """
        if shape1 == "square" and shape2 == "rectangle":
            side = dimensions.get("side", 1)
            area = side * side
            # Transform to rectangle with given length
            length = dimensions.get("length", side)
            width = area / length
            return {"length": length, "width": width, "area": area}
        
        return {"error": "Transformation not supported"}
    
    def verify_pythagorean(self, a: float, b: float, c: float) -> bool:
        """Verify if triple satisfies Pythagorean theorem"""
        return abs(a*a + b*b - c*c) < 0.001
        
    def baudhayana_theorem(self, a: float, b: float) -> float:
        """Calculate diagonal using Baudhayana theorem (c² = a² + b²)."""
        return math.sqrt(a*a + b*b)
    
    def get_triples(self) -> List[Tuple[int, int, int]]:
        """Get all known Pythagorean triples"""
        return self.pythagorean_triples


class AryabhataSystem:
    """
    Āryabhaṭa's mathematical system (आर्यभटीय).
    
    From Āryabhaṭīya (499 CE):
    - Number system
    - Algebra (कुट्टक)
    - Trigonometry (ज्या)
    - Astronomy
    """
    
    def __init__(self):
        # Āryabhaṭa's sine table (ज्या)
        self.sine_table = self._generate_sine_table()
        
        # Āryabhaṭa's π approximation
        self.pi_approx = 3.1416
    
    def _generate_sine_table(self) -> List[float]:
        """
        Generate Āryabhaṭa's sine table.
        
        24 sine differences for quadrant (90° = 5400 minutes)
        """
        # Simplified - actual table uses specific differences
        table = []
        for i in range(24):
            angle_deg = (i + 1) * 3.75  # 90/24 = 3.75
            angle_rad = math.radians(angle_deg)
            table.append(math.sin(angle_rad))
        return table
    
    def get_sine(self, angle_deg: float) -> float:
        """
        Get sine value from Āryabhaṭa's table.
        
        Args:
            angle_deg: Angle in degrees
        
        Returns:
            Sine value (ज्या)
        """
        if angle_deg < 0 or angle_deg > 90:
            # Use symmetry
            angle_deg = angle_deg % 90
        
        index = int(angle_deg / 3.75) - 1
        if index < 0:
            index = 0
        if index >= len(self.sine_table):
            index = len(self.sine_table) - 1
        
        return self.sine_table[index]
    
    def get_pi(self) -> float:
        """Get Āryabhaṭa's π approximation"""
        return self.pi_approx
    
    def solve_kuttaka(self, a: int, b: int, c: int) -> Optional[Tuple[int, int]]:
        """
        Solve linear indeterminate equation (कुट्टक).
        
        ax + by = c
        
        Uses Āryabhaṭa's kuṭṭaka method (pulverizer).
        """
        # Simplified implementation
        # Full implementation uses continued fractions
        gcd, x, y = self._extended_gcd(a, b)
        
        if c % gcd != 0:
            return None  # No solution
        
        multiplier = c // gcd
        return (x * multiplier, y * multiplier)
    
    def _extended_gcd(self, a: int, b: int) -> Tuple[int, int, int]:
        """Extended Euclidean algorithm"""
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = self._extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y
    
    def calculate_area_circle(self, radius: float) -> float:
        """Calculate area of circle using Āryabhaṭa's π"""
        return self.pi_approx * radius * radius
    
    def calculate_circumference(self, diameter: float) -> float:
        """Calculate circumference using Āryabhaṭa's π"""
        return self.pi_approx * diameter


class BrahmaguptaSystem:
    """
    Brahmagupta's mathematical system (ब्रह्मगुप्त).
    
    From Brāhmasphuṭasiddhānta (628 CE):
    - Zero and negative numbers
    - Quadratic equations
    - Cyclic quadrilaterals
    - Series summation
    """
    
    def __init__(self):
        # Brahmagupta's formula for cyclic quadrilateral area
        self.formulas = {
            "cyclic_quadrilateral": "√[(s-a)(s-b)(s-c)(s-d)] where s = (a+b+c+d)/2",
            "quadratic_solution": "x = (√(4ac + b²) - b) / 2a",
            "sum_of_squares": "n(n+1)(2n+1)/6",
            "sum_of_cubes": "[n(n+1)/2]²",
        }
    
    def cyclic_quadrilateral_area(self, a: float, b: float, 
                                   c: float, d: float) -> float:
        """
        Calculate area of cyclic quadrilateral.
        
        Brahmagupta's formula: A = √[(s-a)(s-b)(s-c)(s-d)]
        where s = semi-perimeter
        """
        s = (a + b + c + d) / 2
        area_squared = (s - a) * (s - b) * (s - c) * (s - d)
        
        if area_squared < 0:
            return 0.0  # Invalid quadrilateral
        
        return math.sqrt(area_squared)
    
    def solve_quadratic(self, a: float, b: float, c: float) -> List[float]:
        """
        Solve quadratic equation ax² + bx + c = 0.
        
        Uses Brahmagupta's method.
        """
        discriminant = b*b - 4*a*c
        
        if discriminant < 0:
            return []  # No real solutions
        elif discriminant == 0:
            return [-b / (2*a)]
        else:
            sqrt_d = math.sqrt(discriminant)
            return [(-b + sqrt_d) / (2*a), (-b - sqrt_d) / (2*a)]
    
    def sum_of_squares(self, n: int) -> int:
        """Calculate sum of first n squares"""
        return n * (n + 1) * (2*n + 1) // 6
    
    def sum_of_cubes(self, n: int) -> int:
        """Calculate sum of first n cubes"""
        triangular = n * (n + 1) // 2
        return triangular * triangular
    
    def sum_of_naturals(self, n: int) -> int:
        """Calculate sum of first n natural numbers"""
        return n * (n + 1) // 2
    
    def zero_rules(self) -> Dict:
        """Get Brahmagupta's rules for zero"""
        return {
            "addition": "a + 0 = a",
            "subtraction": "a - 0 = a",
            "multiplication": "a × 0 = 0",
            "division": "a ÷ 0 = undefined (Brahmagupta said a/0 = 0, but this is incorrect)",
            "negative": "0 - a = -a",
        }
    
    def negative_rules(self) -> Dict:
        """Get Brahmagupta's rules for negative numbers"""
        return {
            "addition": "(-a) + (-b) = -(a+b)",
            "subtraction": "(-a) - (-b) = b - a",
            "multiplication": "(-a) × (-b) = ab",
            "division": "(-a) ÷ (-b) = a/b",
        }


class GanitaEngine:
    """
    Complete Gaṇita engine integrating all mathematical systems.
    
    Provides:
    - Geometry (Śulba)
    - Algebra (Āryabhaṭa, Brahmagupta)
    - Arithmetic
    - Series
    """
    
    def __init__(self):
        self.sulba = SulbaGeometry()
        self.aryabhata = AryabhataSystem()
        self.brahmagupta = BrahmaguptaSystem()
    
    def calculate(self, operation: str, **kwargs) -> float:
        """
        Perform mathematical calculation.
        
        Operations:
        - square_root, sine, pi, area_circle, circumference
        - quadratic_solve, cyclic_area, sum_squares, sum_cubes
        """
        if operation == "square_root":
            return self.sulba.calculate_square_root(kwargs.get("n", 1))
        elif operation == "sine":
            return self.aryabhata.get_sine(kwargs.get("angle", 0))
        elif operation == "pi":
            return self.aryabhata.get_pi()
        elif operation == "area_circle":
            return self.aryabhata.calculate_area_circle(kwargs.get("radius", 1))
        elif operation == "circumference":
            return self.aryabhata.calculate_circumference(kwargs.get("diameter", 1))
        elif operation == "quadratic_solve":
            return self.brahmagupta.solve_quadratic(
                kwargs.get("a", 1),
                kwargs.get("b", 0),
                kwargs.get("c", 0)
            )
        elif operation == "cyclic_area":
            return self.brahmagupta.cyclic_quadrilateral_area(
                kwargs.get("a", 1),
                kwargs.get("b", 1),
                kwargs.get("c", 1),
                kwargs.get("d", 1)
            )
        elif operation == "sum_squares":
            return self.brahmagupta.sum_of_squares(kwargs.get("n", 1))
        elif operation == "sum_cubes":
            return self.brahmagupta.sum_of_cubes(kwargs.get("n", 1))
        
        return 0.0
    
    def get_formula(self, topic: str) -> str:
        """Get mathematical formula"""
        if topic == "pythagorean":
            return "c² = a² + b² (Baudhāyana Śulba Sūtra 1.12)"
        elif topic == "cyclic_quadrilateral":
            return self.brahmagupta.formulas["cyclic_quadrilateral"]
        elif topic == "quadratic":
            return self.brahmagupta.formulas["quadratic_solution"]
        
        return "Formula not found"


# Signature
SIGNATURE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    *Visionary RM (Raj Mitra)* ⚡                             ║
║             "Gaṇita Module - Complete Mathematics Engine" 🔱                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
Ganita = GanitaEngine
