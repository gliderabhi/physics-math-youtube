"""
Seed initial problem collections for subtopics in subtopic_problems table.
"""
import json
from generator.db import get_conn

PROBLEMS_DATA = [
    # -------------------------------------------------------------
    # MATH: Algebraic Identities (10 Problems)
    # -------------------------------------------------------------
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 1,
        "title": "Sum & Difference of Reciprocal Squares",
        "problem_statement": "If x + 1/x = 5, find the exact numerical value of x^2 + 1/x^2.",
        "steps": [
            {
                "label": "Step 1: Square both sides",
                "text": "Start with the given equation and square both sides to generate the quadratic terms.",
                "latex": "\\left(x + \\dfrac{1}{x}\\right)^2 = 5^2",
            },
            {
                "label": "Step 2: Expand using identity",
                "text": "Apply the identity (a + b)^2 = a^2 + 2ab + b^2. The cross term x * (1/x) simplifies to 1.",
                "latex": "x^2 + 2\\cdot x \\cdot \\dfrac{1}{x} + \\dfrac{1}{x^2} = 25 \\implies x^2 + 2 + \\dfrac{1}{x^2} = 25",
            },
            {
                "label": "Step 3: Isolate x^2 + 1/x^2",
                "text": "Subtract 2 from both sides of the equation to obtain the desired expression.",
                "latex": "x^2 + \\dfrac{1}{x^2} = 25 - 2 = 23",
            },
        ],
        "final_answer": "The value of x^2 + 1/x^2 is 23.",
        "final_answer_latex": "x^2 + \\dfrac{1}{x^2} = 23",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 2,
        "title": "Reverse Square Identity: Finding Difference",
        "problem_statement": "If x^2 + 1/x^2 = 38, find the value of x - 1/x (given x > 1).",
        "steps": [
            {
                "label": "Step 1: Recall difference identity",
                "text": "Recall the identity for (x - 1/x)^2 and express it in terms of x^2 + 1/x^2.",
                "latex": "\\left(x - \\dfrac{1}{x}\\right)^2 = x^2 - 2\\cdot x \\cdot \\dfrac{1}{x} + \\dfrac{1}{x^2} = x^2 + \\dfrac{1}{x^2} - 2",
            },
            {
                "label": "Step 2: Substitute given value",
                "text": "Substitute x^2 + 1/x^2 = 38 into the identity.",
                "latex": "\\left(x - \\dfrac{1}{x}\\right)^2 = 38 - 2 = 36",
            },
            {
                "label": "Step 3: Take square root",
                "text": "Since x > 1, x > 1/x, so x - 1/x must be positive.",
                "latex": "x - \\dfrac{1}{x} = \\sqrt{36} = 6",
            },
        ],
        "final_answer": "The value of x - 1/x is 6.",
        "final_answer_latex": "x - \\dfrac{1}{x} = 6",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 3,
        "title": "Difference of Consecutive Large Squares",
        "problem_statement": "Evaluate 2026^2 - 2025^2 without long multiplication.",
        "steps": [
            {
                "label": "Step 1: Apply difference of squares identity",
                "text": "Use the standard identity a^2 - b^2 = (a - b)(a + b) with a = 2026 and b = 2025.",
                "latex": "2026^2 - 2025^2 = (2026 - 2025)(2026 + 2025)",
            },
            {
                "label": "Step 2: Compute factors",
                "text": "The difference between consecutive numbers is 1, and their sum is easy to compute.",
                "latex": "2026 - 2025 = 1, \\quad 2026 + 2025 = 4051",
            },
            {
                "label": "Step 3: Multiply results",
                "text": "Multiply the two factors together.",
                "latex": "1 \\times 4051 = 4051",
            },
        ],
        "final_answer": "2026^2 - 2025^2 = 4051.",
        "final_answer_latex": "2026^2 - 2025^2 = 4051",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 4,
        "title": "Sum of Cubes from Sum & Product",
        "problem_statement": "If a + b = 6 and ab = 8, find the value of a^3 + b^3.",
        "steps": [
            {
                "label": "Step 1: Write cubic identity",
                "text": "Express the sum of cubes using the sum and product identity.",
                "latex": "a^3 + b^3 = (a + b)^3 - 3ab(a + b)",
            },
            {
                "label": "Step 2: Substitute values",
                "text": "Substitute a + b = 6 and ab = 8 into the formula.",
                "latex": "a^3 + b^3 = 6^3 - 3(8)(6)",
            },
            {
                "label": "Step 3: Simplify arithmetic",
                "text": "Calculate 6^3 = 216 and 3 * 8 * 6 = 144, then subtract.",
                "latex": "a^3 + b^3 = 216 - 144 = 72",
            },
        ],
        "final_answer": "The sum of cubes a^3 + b^3 is 72.",
        "final_answer_latex": "a^3 + b^3 = 72",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 5,
        "title": "Conditional Cube Identity when a + b + c = 0",
        "problem_statement": "Evaluate (28)^3 + (-15)^3 + (-13)^3 without calculating individual cubes.",
        "steps": [
            {
                "label": "Step 1: Check the zero-sum condition",
                "text": "Let a = 28, b = -15, and c = -13. Verify if their sum equals zero.",
                "latex": "a + b + c = 28 + (-15) + (-13) = 28 - 28 = 0",
            },
            {
                "label": "Step 2: Apply conditional identity",
                "text": "Whenever a + b + c = 0, the identity states that a^3 + b^3 + c^3 = 3abc.",
                "latex": "a^3 + b^3 + c^3 = 3abc",
            },
            {
                "label": "Step 3: Compute the product 3abc",
                "text": "Substitute the numbers into 3abc.",
                "latex": "3 \\times (28) \\times (-15) \\times (-13) = 84 \\times 195 = 16380",
            },
        ],
        "final_answer": "The value of (28)^3 + (-15)^3 + (-13)^3 is 16380.",
        "final_answer_latex": "(28)^3 + (-15)^3 + (-13)^3 = 16380",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 6,
        "title": "Sum of Squares of a Trinomial",
        "problem_statement": "If a + b + c = 9 and ab + bc + ca = 26, find the value of a^2 + b^2 + c^2.",
        "steps": [
            {
                "label": "Step 1: Recall trinomial expansion",
                "text": "Use the identity for the square of a trinomial.",
                "latex": "(a + b + c)^2 = a^2 + b^2 + c^2 + 2(ab + bc + ca)",
            },
            {
                "label": "Step 2: Substitute known quantities",
                "text": "Plug in a + b + c = 9 and ab + bc + ca = 26.",
                "latex": "9^2 = (a^2 + b^2 + c^2) + 2(26)",
            },
            {
                "label": "Step 3: Solve for a^2 + b^2 + c^2",
                "text": "Subtract 52 from 81.",
                "latex": "81 = (a^2 + b^2 + c^2) + 52 \\implies a^2 + b^2 + c^2 = 81 - 52 = 29",
            },
        ],
        "final_answer": "a^2 + b^2 + c^2 = 29.",
        "final_answer_latex": "a^2 + b^2 + c^2 = 29",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 7,
        "title": "Fourth-Power Leap: x^4 + 1/x^4",
        "problem_statement": "If x + 1/x = 3, determine the value of x^4 + 1/x^4.",
        "steps": [
            {
                "label": "Step 1: First squaring (degree 2)",
                "text": "Square both sides of x + 1/x = 3.",
                "latex": "\\left(x + \\dfrac{1}{x}\\right)^2 = 3^2 \\implies x^2 + 2 + \\dfrac{1}{x^2} = 9 \\implies x^2 + \\dfrac{1}{x^2} = 7",
            },
            {
                "label": "Step 2: Second squaring (degree 4)",
                "text": "Now square the obtained expression x^2 + 1/x^2 = 7.",
                "latex": "\\left(x^2 + \\dfrac{1}{x^2}\\right)^2 = 7^2 \\implies x^4 + 2 + \\dfrac{1}{x^4} = 49",
            },
            {
                "label": "Step 3: Subtract cross term",
                "text": "Subtract 2 from 49 to isolate x^4 + 1/x^4.",
                "latex": "x^4 + \\dfrac{1}{x^4} = 49 - 2 = 47",
            },
        ],
        "final_answer": "x^4 + 1/x^4 = 47.",
        "final_answer_latex": "x^4 + \\dfrac{1}{x^4} = 47",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 8,
        "title": "Fifth-Power Symmetry: x^5 + 1/x^5",
        "problem_statement": "If x + 1/x = 3, find the value of x^5 + 1/x^5.",
        "steps": [
            {
                "label": "Step 1: Calculate quadratic and cubic terms",
                "text": "From x + 1/x = 3: x^2 + 1/x^2 = 7 and x^3 + 1/x^3 = 3^3 - 3(3) = 18.",
                "latex": "x^2 + \\dfrac{1}{x^2} = 7, \\quad x^3 + \\dfrac{1}{x^3} = 18",
            },
            {
                "label": "Step 2: Multiply quadratic and cubic expressions",
                "text": "Multiply (x^2 + 1/x^2) by (x^3 + 1/x^3) to produce power 5 terms.",
                "latex": "\\left(x^2 + \\dfrac{1}{x^2}\\right)\\left(x^3 + \\dfrac{1}{x^3}\\right) = x^5 + \\dfrac{1}{x^5} + \\left(x + \\dfrac{1}{x}\\right)",
            },
            {
                "label": "Step 3: Solve for fifth power",
                "text": "Substitute the known values into the equation.",
                "latex": "7 \\times 18 = x^5 + \\dfrac{1}{x^5} + 3 \\implies 126 = x^5 + \\dfrac{1}{x^5} + 3 \\implies x^5 + \\dfrac{1}{x^5} = 123",
            },
        ],
        "final_answer": "x^5 + 1/x^5 = 123.",
        "final_answer_latex": "x^5 + \\dfrac{1}{x^5} = 123",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 9,
        "title": "Sophie Germain Factorization of x^4 + 4y^4",
        "problem_statement": "Factorize x^4 + 4y^4 into a product of two real quadratic factors.",
        "steps": [
            {
                "label": "Step 1: Complete the square",
                "text": "Add and subtract 4x^2 y^2 to create a perfect trinomial square.",
                "latex": "x^4 + 4y^4 = (x^2)^2 + 2(x^2)(2y^2) + (2y^2)^2 - 4x^2 y^2",
            },
            {
                "label": "Step 2: Rewrite as difference of squares",
                "text": "Express the expression as A^2 - B^2 where A = x^2 + 2y^2 and B = 2xy.",
                "latex": "= (x^2 + 2y^2)^2 - (2xy)^2",
            },
            {
                "label": "Step 3: Apply A^2 - B^2 = (A - B)(A + B)",
                "text": "Factorize into the two real quadratic expressions.",
                "latex": "= (x^2 - 2xy + 2y^2)(x^2 + 2xy + 2y^2)",
            },
        ],
        "final_answer": "x^4 + 4y^4 = (x^2 - 2xy + 2y^2)(x^2 + 2xy + 2y^2).",
        "final_answer_latex": "(x^2 - 2xy + 2y^2)(x^2 + 2xy + 2y^2)",
        "visual_type": "algebra_geometry",
    },
    {
        "subject": "math",
        "chapter": "Polynomials",
        "subtopic": "Algebraic identities",
        "problem_index": 10,
        "title": "Sum of Squares Equality: Proving a = b = c",
        "problem_statement": "If a, b, c are real numbers and a^2 + b^2 + c^2 = ab + bc + ca, prove that a = b = c.",
        "steps": [
            {
                "label": "Step 1: Double both sides and rearrange",
                "text": "Multiply the entire equation by 2 and bring all terms to the left-hand side.",
                "latex": "2a^2 + 2b^2 + 2c^2 - 2ab - 2bc - 2ca = 0",
            },
            {
                "label": "Step 2: Group into three perfect squares",
                "text": "Group terms: (a^2 - 2ab + b^2) + (b^2 - 2bc + c^2) + (c^2 - 2ca + a^2).",
                "latex": "(a - b)^2 + (b - c)^2 + (c - a)^2 = 0",
            },
            {
                "label": "Step 3: Deduce equality",
                "text": "Since each term is a real square (>= 0), their sum is zero only if each term is zero.",
                "latex": "a - b = 0, \\; b - c = 0, \\; c - a = 0 \\implies a = b = c",
            },
        ],
        "final_answer": "Since (a-b)^2 + (b-c)^2 + (c-a)^2 = 0 for real numbers, a = b = c.",
        "final_answer_latex": "a = b = c",
        "visual_type": "algebra_geometry",
    },

    # Also mirror the math problems for Class 9 Algebraic Identities -> Standard identities...
    {
        "subject": "math",
        "chapter": "Algebraic Identities",
        "subtopic": "Standard identities: (a+b)^2, (a-b)^2, a^2-b^2",
        "problem_index": 1,
        "title": "Sum & Difference of Reciprocal Squares",
        "problem_statement": "If x + 1/x = 5, find the exact numerical value of x^2 + 1/x^2.",
        "steps": [
            {
                "label": "Step 1: Square both sides",
                "text": "Start with the given equation and square both sides to generate the quadratic terms.",
                "latex": "\\left(x + \\dfrac{1}{x}\\right)^2 = 5^2",
            },
            {
                "label": "Step 2: Expand using identity",
                "text": "Apply the identity (a + b)^2 = a^2 + 2ab + b^2. The cross term x * (1/x) simplifies to 1.",
                "latex": "x^2 + 2\\cdot x \\cdot \\dfrac{1}{x} + \\dfrac{1}{x^2} = 25 \\implies x^2 + 2 + \\dfrac{1}{x^2} = 25",
            },
            {
                "label": "Step 3: Isolate x^2 + 1/x^2",
                "text": "Subtract 2 from both sides of the equation to obtain the desired expression.",
                "latex": "x^2 + \\dfrac{1}{x^2} = 25 - 2 = 23",
            },
        ],
        "final_answer": "The value of x^2 + 1/x^2 is 23.",
        "final_answer_latex": "x^2 + \\dfrac{1}{x^2} = 23",
        "visual_type": "algebra_geometry",
    },

    # -------------------------------------------------------------
    # CHEMISTRY: Acids, Bases and Salts (5 Problems)
    # -------------------------------------------------------------
    {
        "subject": "chemistry",
        "chapter": "Acids Bases and Salts",
        "subtopic": "pH Scale and Importance in Everyday Life",
        "problem_index": 1,
        "title": "pH Calculation of Strong Monoprotic Acid",
        "problem_statement": "Calculate the pH of a 0.001 M aqueous solution of hydrochloric acid (HCl).",
        "steps": [
            {
                "label": "Step 1: Determine hydrogen ion concentration",
                "text": "HCl is a strong acid and completely dissociates in water: HCl -> H+ + Cl-.",
                "latex": "[\\text{H}^+] = 0.001\\text{ M} = 10^{-3}\\text{ M}",
            },
            {
                "label": "Step 2: Apply pH definition",
                "text": "pH is defined as the negative logarithm of hydronium/hydrogen ion concentration.",
                "latex": "\\text{pH} = -\\log_{10}[\\text{H}^+]",
            },
            {
                "label": "Step 3: Calculate logarithmic value",
                "text": "Substitute [H+] = 10^-3 M into the logarithmic expression.",
                "latex": "\\text{pH} = -\\log_{10}(10^{-3}) = -(-3) = 3",
            },
        ],
        "final_answer": "The pH of the solution is 3, indicating a strongly acidic solution.",
        "final_answer_latex": "\\text{pH} = 3",
        "visual_type": "ph_scale",
    },
    {
        "subject": "chemistry",
        "chapter": "Acids Bases and Salts",
        "subtopic": "pH Scale and Importance in Everyday Life",
        "problem_index": 2,
        "title": "The Ultra-Dilute Acid Trap: pH of 10^-8 M HCl",
        "problem_statement": "Why is the pH of a 10^-8 M HCl aqueous solution NOT 8? Calculate its true pH at 25°C.",
        "steps": [
            {
                "label": "Step 1: Identify the chemical contradiction",
                "text": "An acidic solution cannot have a basic pH (> 7) at 25°C. Water's auto-ionization cannot be ignored.",
                "latex": "[\\text{H}^+]_{\\text{water}} = 10^{-7}\\text{ M} > [\\text{H}^+]_{\\text{acid}} = 10^{-8}\\text{ M}",
            },
            {
                "label": "Step 2: Account for total hydrogen ion concentration",
                "text": "Sum the H+ contribution from the acid and water.",
                "latex": "[\\text{H}^+]_{\\text{total}} = 10^{-8} + 10^{-7} = 1.1 \\times 10^{-7}\\text{ M}",
            },
            {
                "label": "Step 3: Compute actual pH",
                "text": "Take the negative log of total [H+].",
                "latex": "\\text{pH} = -\\log_{10}(1.1 \\times 10^{-7}) = 7 - \\log_{10}(1.1) \\approx 7 - 0.04 = 6.96",
            },
        ],
        "final_answer": "The true pH is approximately 6.96, remaining acidic (just below 7).",
        "final_answer_latex": "\\text{pH} \\approx 6.96",
        "visual_type": "ph_scale",
    },
    {
        "subject": "chemistry",
        "chapter": "Acids Bases and Salts",
        "subtopic": "pH Scale and Importance in Everyday Life",
        "problem_index": 3,
        "title": "Neutralization Titration Volume",
        "problem_statement": "What volume of 0.1 M NaOH is required to completely neutralize 25 mL of 0.2 M H2SO4?",
        "steps": [
            {
                "label": "Step 1: Balanced chemical equation",
                "text": "Write the neutralization stoichiometry between sulfuric acid (diprotic) and sodium hydroxide.",
                "latex": "\\text{H}_2\\text{SO}_4 + 2\\text{NaOH} \\longrightarrow \\text{Na}_2\\text{SO}_4 + 2\\text{H}_2\\text{O}",
            },
            {
                "label": "Step 2: Compute moles of acid",
                "text": "Moles of H2SO4 = Molarity * Volume in liters.",
                "latex": "n_{\\text{acid}} = 0.2\\text{ M} \\times 0.025\\text{ L} = 0.005\\text{ mol}",
            },
            {
                "label": "Step 3: Compute moles of NaOH and volume",
                "text": "Each mole of H2SO4 requires 2 moles of NaOH.",
                "latex": "n_{\\text{base}} = 2 \\times 0.005 = 0.010\\text{ mol} \\implies V_{\\text{base}} = \\dfrac{0.010\\text{ mol}}{0.1\\text{ M}} = 0.1\\text{ L} = 100\\text{ mL}",
            },
        ],
        "final_answer": "100 mL of 0.1 M NaOH is required.",
        "final_answer_latex": "V_{\\text{NaOH}} = 100\\text{ mL}",
        "visual_type": "titration_burette",
    },
    {
        "subject": "chemistry",
        "chapter": "Acids Bases and Salts",
        "subtopic": "pH Scale and Importance in Everyday Life",
        "problem_index": 4,
        "title": "pH of a Strong Base: 0.01 M NaOH",
        "problem_statement": "Find the pH of a 0.01 M sodium hydroxide (NaOH) solution at 25°C.",
        "steps": [
            {
                "label": "Step 1: Find hydroxide concentration [OH-]",
                "text": "NaOH completely dissociates into Na+ and OH- in aqueous solution.",
                "latex": "[\\text{OH}^-] = 0.01\\text{ M} = 10^{-2}\\text{ M}",
            },
            {
                "label": "Step 2: Calculate pOH",
                "text": "pOH is the negative log of hydroxide ion concentration.",
                "latex": "\\text{pOH} = -\\log_{10}[\\text{OH}^-] = -\\log_{10}(10^{-2}) = 2",
            },
            {
                "label": "Step 3: Convert pOH to pH",
                "text": "At 25°C, the ionic product of water dictates that pH + pOH = 14.",
                "latex": "\\text{pH} = 14 - \\text{pOH} = 14 - 2 = 12",
            },
        ],
        "final_answer": "The pH of the NaOH solution is 12 (strongly basic).",
        "final_answer_latex": "\\text{pH} = 12",
        "visual_type": "ph_scale",
    },
    {
        "subject": "chemistry",
        "chapter": "Acids Bases and Salts",
        "subtopic": "pH Scale and Importance in Everyday Life",
        "problem_index": 5,
        "title": "Salt Hydrolysis and Solution Acidity",
        "problem_statement": "Predict whether an aqueous solution of ammonium chloride (NH4Cl) is acidic, basic, or neutral, and state why.",
        "steps": [
            {
                "label": "Step 1: Identify parent acid and base",
                "text": "NH4Cl is formed by neutralizing hydrochloric acid (strong acid) with ammonium hydroxide (weak base).",
                "latex": "\\text{HCl (Strong Acid)} + \\text{NH}_4\\text{OH (Weak Base)} \\longrightarrow \\text{NH}_4\\text{Cl} + \\text{H}_2\\text{O}",
            },
            {
                "label": "Step 2: Analyze ionic hydrolysis",
                "text": "The chloride ion (Cl-) does not hydrolyze, but the ammonium cation (NH4+) reacts with water molecules.",
                "latex": "\\text{NH}_4^+ + \\text{H}_2\\text{O} \\rightleftharpoons \\text{NH}_3 + \\text{H}_3\\text{O}^+",
            },
            {
                "label": "Step 3: Determine pH character",
                "text": "Production of hydronium ions (H3O+) creates an excess of H+ over OH-.",
                "latex": "[\\text{H}_3\\text{O}^+] > [\\text{OH}^-] \\implies \\text{pH} < 7",
            },
        ],
        "final_answer": "The solution is acidic with a pH less than 7 due to cationic hydrolysis of NH4+.",
        "final_answer_latex": "\\text{Acidic } (\\text{pH} < 7)",
        "visual_type": "ph_scale",
    },

    # -------------------------------------------------------------
    # PHYSICS: Electricity (12 Problems)
    # -------------------------------------------------------------
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 1,
        "title": "Series-Parallel Equivalent Resistance",
        "problem_statement": "Three identical 6 ohm resistors are connected such that two are in parallel, and this pair is connected in series with the third. Find the total equivalent resistance.",
        "steps": [
            {
                "label": "Step 1: Solve the parallel branch",
                "text": "Calculate equivalent resistance Rp of the two 6 ohm resistors connected in parallel.",
                "latex": "\\dfrac{1}{R_p} = \\dfrac{1}{6} + \\dfrac{1}{6} = \\dfrac{2}{6} \\implies R_p = 3\\,\\Omega",
            },
            {
                "label": "Step 2: Add the series resistor",
                "text": "The parallel combination Rp is in series with the third 6 ohm resistor.",
                "latex": "R_{\\text{eq}} = R_p + R_3 = 3\\,\\Omega + 6\\,\\Omega = 9\\,\\Omega",
            },
        ],
        "final_answer": "The equivalent resistance is 9 ohms.",
        "final_answer_latex": "R_{\\text{eq}} = 9\\,\\Omega",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 2,
        "title": "Infinite Resistor Ladder Network",
        "problem_statement": "Find the equivalent resistance between terminals A and B of an infinite ladder composed of 1 ohm resistors.",
        "steps": [
            {
                "label": "Step 1: Self-similarity property",
                "text": "Since the ladder is infinite, removing the first unit leaves an identical infinite ladder of resistance Req.",
                "latex": "R_{\\text{eq}} = 1 + (1 \\parallel R_{\\text{eq}})",
            },
            {
                "label": "Step 2: Form quadratic equation",
                "text": "Express the parallel combination and clear the fraction.",
                "latex": "R_{\\text{eq}} = 1 + \\dfrac{R_{\\text{eq}}}{1 + R_{\\text{eq}}} \\implies R_{\\text{eq}}^2 - R_{\\text{eq}} - 1 = 0",
            },
            {
                "label": "Step 3: Solve quadratic for positive root",
                "text": "Resistance must be strictly positive.",
                "latex": "R_{\\text{eq}} = \\dfrac{1 + \\sqrt{1 + 4(1)}}{2} = \\dfrac{1 + \\sqrt{5}}{2} \\approx 1.618\\,\\Omega",
            },
        ],
        "final_answer": "The equivalent resistance is (1 + sqrt(5))/2 ohms (approx 1.618 ohms, the Golden Ratio).",
        "final_answer_latex": "R_{\\text{eq}} = \\dfrac{1 + \\sqrt{5}}{2}\\,\\Omega \\approx 1.618\\,\\Omega",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 3,
        "title": "Cube of Resistors (Opposite Vertices)",
        "problem_statement": "Twelve identical resistors of resistance R form the edges of a cube. Find Req between diagonally opposite vertices A and B.",
        "steps": [
            {
                "label": "Step 1: Current splitting by symmetry",
                "text": "A total current I entering vertex A splits equally into 3 edges: I/3 per edge.",
                "latex": "I_1 = \\dfrac{I}{3}",
            },
            {
                "label": "Step 2: Intermediate split across 6 edges",
                "text": "At each subsequent node, each I/3 branch splits equally into 2 edges: (I/3)/2 = I/6.",
                "latex": "I_2 = \\dfrac{I}{6}",
            },
            {
                "label": "Step 3: Sum total potential drop",
                "text": "Integrate potential drops from entrance vertex to exit vertex.",
                "latex": "V_{AB} = \\left(\\dfrac{I}{3}\\right)R + \\left(\\dfrac{I}{6}\\right)R + \\left(\\dfrac{I}{3}\\right)R = \\dfrac{5}{6}IR",
            },
            {
                "label": "Step 4: Extract equivalent resistance",
                "text": "By Ohm's law, Req = V_{AB} / I.",
                "latex": "R_{\\text{eq}} = \\dfrac{5}{6}R",
            },
        ],
        "final_answer": "The equivalent resistance between diagonally opposite corners is 5/6 R.",
        "final_answer_latex": "R_{\\text{eq}} = \\dfrac{5}{6}R",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 4,
        "title": "Balanced Wheatstone Bridge",
        "problem_statement": "Resistors of 2, 4, 3, and 6 ohms form the arms of a bridge circuit with a galvanometer connected across opposite junctions. What current flows through the galvanometer?",
        "steps": [
            {
                "label": "Step 1: Check bridge balance condition",
                "text": "Compare the resistance ratio of the left branches with the right branches.",
                "latex": "\\dfrac{R_1}{R_2} = \\dfrac{2}{4} = \\dfrac{1}{2}, \\quad \\dfrac{R_3}{R_4} = \\dfrac{3}{6} = \\dfrac{1}{2}",
            },
            {
                "label": "Step 2: Assess junction potential difference",
                "text": "Since R1/R2 = R3/R4, the potentials at both galvanometer terminals are equal (Vc = Vd).",
                "latex": "V_C - V_D = 0\\text{ V}",
            },
            {
                "label": "Step 3: Deduce bridge current",
                "text": "Zero potential difference means zero current flows through the central galvanometer branch.",
                "latex": "I_g = \\dfrac{V_C - V_D}{R_g} = 0\\text{ A}",
            },
        ],
        "final_answer": "The galvanometer detects zero current (0 A) because the bridge is balanced.",
        "final_answer_latex": "I_g = 0\\text{ A}",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Heating effect of current and electric power",
        "problem_index": 5,
        "title": "Series Bulb Brightness Paradox",
        "problem_statement": "Two light bulbs rated 100 W, 220 V and 40 W, 220 V are connected in series across a 220 V supply. Which bulb glows brighter?",
        "steps": [
            {
                "label": "Step 1: Calculate filament resistances",
                "text": "From rated power P = V^2 / R, resistance is inversely proportional to rated power.",
                "latex": "R_{100} = \\dfrac{220^2}{100} = 484\\,\\Omega, \\quad R_{40} = \\dfrac{220^2}{40} = 1210\\,\\Omega",
            },
            {
                "label": "Step 2: Apply series current condition",
                "text": "In series, the exact same current I passes through both light bulbs.",
                "latex": "P_{\\text{actual}} = I^2 R",
            },
            {
                "label": "Step 3: Compare actual power dissipated",
                "text": "Since R40 > R100, the 40 W bulb dissipates more electrical power as heat and light in series.",
                "latex": "P_{40} = I^2 (1210) > P_{100} = I^2 (484)",
            },
        ],
        "final_answer": "The 40 W bulb glows significantly brighter in a series connection.",
        "final_answer_latex": "P_{40} > P_{100} \\implies \\text{40 W bulb glows brighter}",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Ohm's law and resistance",
        "problem_index": 6,
        "title": "Resistance of a Stretched Wire",
        "problem_statement": "A cylindrical copper wire has resistance 4 ohms. If it is uniformly stretched to double its original length, find its new resistance.",
        "steps": [
            {
                "label": "Step 1: Volume conservation",
                "text": "When a wire is stretched, its total material volume V = A * L remains constant.",
                "latex": "L' = 2L \\implies A' = \\dfrac{A}{2}",
            },
            {
                "label": "Step 2: Formula for electrical resistance",
                "text": "Resistance is proportional to length and inversely proportional to cross-sectional area.",
                "latex": "R = \\rho \\dfrac{L}{A}",
            },
            {
                "label": "Step 3: Compute new resistance",
                "text": "Substitute the new dimensions into the formula.",
                "latex": "R' = \\rho \\dfrac{2L}{A/2} = 4\\left(\\rho \\dfrac{L}{A}\\right) = 4R = 4 \\times 4\\,\\Omega = 16\\,\\Omega",
            },
        ],
        "final_answer": "The new resistance is 16 ohms (increases four-fold).",
        "final_answer_latex": "R' = 16\\,\\Omega",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Heating effect of current and electric power",
        "problem_index": 7,
        "title": "Maximum Power Transfer Theorem",
        "problem_statement": "A battery has an EMF of 12 V and internal resistance of 3 ohms. What is the maximum power it can deliver to an external load resistor RL?",
        "steps": [
            {
                "label": "Step 1: Condition for maximum power",
                "text": "By the maximum power transfer theorem, maximum power is delivered when load resistance equals internal resistance.",
                "latex": "R_L = r = 3\\,\\Omega",
            },
            {
                "label": "Step 2: Circuit current at match",
                "text": "Calculate the current under the matched condition.",
                "latex": "I = \\dfrac{E}{R_L + r} = \\dfrac{12\\text{ V}}{3 + 3\\,\\Omega} = 2\\text{ A}",
            },
            {
                "label": "Step 3: Calculate power dissipated in load",
                "text": "Compute power P = I^2 * RL.",
                "latex": "P_{\\text{max}} = I^2 R_L = (2\\text{ A})^2 \\times 3\\,\\Omega = 4 \\times 3 = 12\\text{ W}",
            },
        ],
        "final_answer": "The maximum power deliverable is 12 W.",
        "final_answer_latex": "P_{\\text{max}} = 12\\text{ W}",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 8,
        "title": "Terminal Voltage of Opposing Battery Cells",
        "problem_statement": "Two batteries, A (10 V, 1 ohm) and B (4 V, 2 ohms), are connected in series with opposing polarity. Find the loop current and terminal voltage of cell B.",
        "steps": [
            {
                "label": "Step 1: Determine net EMF and loop current",
                "text": "Since the cells oppose each other, subtract the smaller EMF from the larger EMF.",
                "latex": "E_{\\text{net}} = 10\\text{ V} - 4\\text{ V} = 6\\text{ V}, \\quad R_{\\text{total}} = 1 + 2 = 3\\,\\Omega",
            },
            {
                "label": "Step 2: Compute current",
                "text": "The larger battery drives current clockwise through both cells.",
                "latex": "I = \\dfrac{6\\text{ V}}{3\\,\\Omega} = 2\\text{ A}",
            },
            {
                "label": "Step 3: Terminal voltage of charging cell B",
                "text": "Since current enters the positive terminal of cell B, it is being charged.",
                "latex": "V_{T, B} = E_B + I r_B = 4\\text{ V} + (2\\text{ A})(2\\,\\Omega) = 4 + 4 = 8\\text{ V}",
            },
        ],
        "final_answer": "Loop current is 2 A, and the terminal voltage of cell B is 8 V.",
        "final_answer_latex": "I = 2\\text{ A}, \\quad V_{T, B} = 8\\text{ V}",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Ohm's law and resistance",
        "problem_index": 9,
        "title": "Determining Battery EMF and Internal Resistance",
        "problem_statement": "A cell delivers 1.5 A through a 2 ohm external resistor, and 1.0 A through a 3.5 ohm resistor. Calculate its EMF E and internal resistance r.",
        "steps": [
            {
                "label": "Step 1: Set up system of equations",
                "text": "Use Ohm's law E = I(R + r) for both loading conditions.",
                "latex": "E = 1.5(2 + r) = 3 + 1.5r \\quad \\text{and} \\quad E = 1.0(3.5 + r) = 3.5 + r",
            },
            {
                "label": "Step 2: Equate equations to solve for r",
                "text": "Eliminate E by equating both expressions.",
                "latex": "3 + 1.5r = 3.5 + r \\implies 0.5r = 0.5 \\implies r = 1.0\\,\\Omega",
            },
            {
                "label": "Step 3: Solve for EMF E",
                "text": "Substitute r = 1 ohm back into either equation.",
                "latex": "E = 1.0(3.5 + 1.0) = 4.5\\text{ V}",
            },
        ],
        "final_answer": "The cell has an EMF of 4.5 V and internal resistance of 1 ohm.",
        "final_answer_latex": "E = 4.5\\text{ V}, \\quad r = 1.0\\,\\Omega",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Series and parallel combination of resistors",
        "problem_index": 10,
        "title": "Meter Bridge Null Point Resistance",
        "problem_statement": "In a meter bridge experiment, a null point is obtained at 40 cm when unknown resistor X is in the left gap and 6 ohm is in the right gap. Find X.",
        "steps": [
            {
                "label": "Step 1: Meter bridge balance condition",
                "text": "In a 100 cm uniform resistance wire, resistance is proportional to wire segment length.",
                "latex": "\\dfrac{X}{R} = \\dfrac{l}{100 - l}",
            },
            {
                "label": "Step 2: Substitute given lengths and resistor",
                "text": "Left wire length is 40 cm, so right wire length is 100 - 40 = 60 cm.",
                "latex": "\\dfrac{X}{6} = \\dfrac{40}{60} = \\dfrac{2}{3}",
            },
            {
                "label": "Step 3: Solve for unknown resistor X",
                "text": "Multiply both sides by 6.",
                "latex": "X = 6 \\times \\dfrac{2}{3} = 4\\,\\Omega",
            },
        ],
        "final_answer": "The unknown resistance X is 4 ohms.",
        "final_answer_latex": "X = 4\\,\\Omega",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Ohm's law and resistance",
        "problem_index": 11,
        "title": "Capacitive Charge Sharing & Voltage Equalization",
        "problem_statement": "A 6 microfarad capacitor charged to 100 V is disconnected and connected in parallel with an uncharged 3 microfarad capacitor. Find the common terminal voltage.",
        "steps": [
            {
                "label": "Step 1: Conservation of initial electrostatic charge",
                "text": "Calculate initial charge stored on the 6 microfarad capacitor.",
                "latex": "Q_1 = C_1 V_1 = (6\\,\\mu\\text{F})(100\\text{ V}) = 600\\,\\mu\\text{C}",
            },
            {
                "label": "Step 2: Equivalent parallel capacitance",
                "text": "In parallel, capacitances add directly.",
                "latex": "C_{\\text{total}} = C_1 + C_2 = 6 + 3 = 9\\,\\mu\\text{F}",
            },
            {
                "label": "Step 3: Calculate common potential",
                "text": "Divide total conserved charge by total capacitance.",
                "latex": "V_{\\text{common}} = \\dfrac{Q_{\\text{total}}}{C_{\\text{total}}} = \\dfrac{600\\,\\mu\\text{C}}{9\\,\\mu\\text{F}} = \\dfrac{200}{3}\\text{ V} \\approx 66.7\\text{ V}",
            },
        ],
        "final_answer": "The final common potential difference across both capacitors is 66.7 V.",
        "final_answer_latex": "V_{\\text{common}} = \\dfrac{200}{3}\\text{ V} \\approx 66.7\\text{ V}",
        "visual_type": "circuit_schematic",
    },
    {
        "subject": "physics",
        "chapter": "Electricity",
        "subtopic": "Ohm's law and resistance",
        "problem_index": 12,
        "title": "RC Circuit Discharge Time Constant",
        "problem_statement": "A 2 microfarad capacitor discharges through a 500 kilo-ohm resistor. How much time does it take for the capacitor voltage to decrease to 37% of its initial charge voltage?",
        "steps": [
            {
                "label": "Step 1: Exponential decay formula",
                "text": "The voltage during capacitive discharge follows V(t) = V0 * e^(-t / RC).",
                "latex": "V(t) = V_0 e^{-t / \\tau}, \\quad \\tau = RC",
            },
            {
                "label": "Step 2: Recognize the 37% milestone",
                "text": "1/e is approximately 0.368 (37%). This voltage is reached exactly at t = tau (one time constant).",
                "latex": "\\dfrac{V(t)}{V_0} = e^{-1} \\approx 0.368 \\implies t = \\tau = RC",
            },
            {
                "label": "Step 3: Calculate numerical time constant",
                "text": "Multiply resistance and capacitance in standard SI units.",
                "latex": "t = (500 \\times 10^3\\,\\Omega) \\times (2 \\times 10^{-6}\\text{ F}) = 1.0\\text{ second}",
            },
        ],
        "final_answer": "The voltage reaches 37% of its initial value in exactly 1.0 second.",
        "final_answer_latex": "t = 1.0\\text{ s}",
        "visual_type": "circuit_schematic",
    },
]


def seed():
    with get_conn() as conn, conn.cursor() as cur:
        for p in PROBLEMS_DATA:
            cur.execute(
                """
                INSERT INTO subtopic_problems (
                    subject, chapter, subtopic, problem_index, title, problem_statement,
                    steps, final_answer, final_answer_latex, visual_type, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    problem_statement = VALUES(problem_statement),
                    steps = VALUES(steps),
                    final_answer = VALUES(final_answer),
                    final_answer_latex = VALUES(final_answer_latex),
                    visual_type = VALUES(visual_type),
                    status = VALUES(status)
                """,
                (
                    p["subject"],
                    p["chapter"],
                    p["subtopic"],
                    p["problem_index"],
                    p["title"],
                    p["problem_statement"],
                    json.dumps(p["steps"]),
                    p["final_answer"],
                    p["final_answer_latex"],
                    p["visual_type"],
                    "available",
                ),
            )
        print(f"Successfully seeded {len(PROBLEMS_DATA)} subtopic problems into subtopic_problems table.")


if __name__ == "__main__":
    seed()
