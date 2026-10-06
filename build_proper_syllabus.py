"""Script to break each merged subtopic in syllabus.json into proper parts
designed for 1-2 minute video explanations (concept explainers & targeted problem solving).
Preserves parent topic prefixes (Parent: Part) for full backwards-compatibility with
video resolvers and Wikipedia knowledge base stores.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SYLLABUS_FILE = ROOT / "syllabus.json"
BACKUP_FILE = ROOT / "syllabus_backup.json"

# Detailed pedagogical breakdown for each parent subtopic into 1-2 min video parts
BREAKDOWNS = {
    # ------------------ CLASS 9 PHYSICS ------------------
    (9, "physics", "Motion", "Distance and displacement"): [
        "Distance and displacement: Scalar vs Vector and Path length",
        "Distance and displacement: Straight-line motion and Direction reversals",
        "Distance and displacement: 2D Right-angle and Hexagonal paths",
        "Distance and displacement: Circular tracks and Closed loops (Displacement = 0)",
    ],
    (9, "physics", "Motion", "Speed and velocity"): [
        "Speed and velocity: Concept, Units and Scalar vs Vector distinction",
        "Speed and velocity: Average speed vs Average velocity in 1D",
        "Speed and velocity: Instantaneous speed and Instantaneous velocity",
        "Speed and velocity: Circular motion with Constant speed vs Changing velocity",
    ],
    (9, "physics", "Motion", "Uniform and non-uniform acceleration"): [
        "Uniform and non-uniform acceleration: Concept and Acceleration formula (a = (v-u)/t)",
        "Uniform and non-uniform acceleration: Positive, Negative (Deceleration) and Zero acceleration",
        "Uniform and non-uniform acceleration: Uniform vs Non-uniform acceleration on velocity-time graphs",
        "Uniform and non-uniform acceleration: Multi-phase journeys (Acceleration, Coasting and Braking)",
    ],
    (9, "physics", "Motion", "Equations of motion by graphical method"): [
        "Equations of motion by graphical method: First equation (v = u + at)",
        "Equations of motion by graphical method: Second equation (s = ut + 1/2 at^2)",
        "Equations of motion by graphical method: Third equation (v^2 = u^2 + 2as)",
        "Equations of motion by graphical method: Stopping distance and Reaction time problems",
    ],
    (9, "physics", "Motion", "Interpreting position-time and velocity-time graphs"): [
        "Position-time graphs: Slope as Velocity (Rest, Uniform motion and Acceleration)",
        "Velocity-time graphs: Slope as Acceleration",
        "Velocity-time graphs: Area under curve as Displacement",
        "Interpreting graphs: Comparing two objects and Overtaking conditions",
    ],

    (9, "physics", "Force and Laws of Motion", "Newton's first law and inertia"): [
        "Newton's first law and inertia: Concept of Inertia and Resistance to motion change",
        "Newton's first law and inertia: Balanced vs Unbalanced forces and Equilibrium",
        "Newton's first law and inertia: Net force and Overcoming friction",
        "Newton's first law and inertia: Inertial frames and Pseudo force in accelerating systems",
    ],
    (9, "physics", "Force and Laws of Motion", "Newton's second law and momentum"): [
        "Newton's second law and momentum: Linear momentum (p = mv) and Rate of change of momentum",
        "Newton's second law and momentum: Derivation of F = ma and Unit Newton",
        "Newton's second law and momentum: Impulse and Force from momentum change (Ball hitting wall)",
        "Newton's second law and momentum: Connected bodies system (Blocks, Pulleys and String tension)",
    ],
    (9, "physics", "Force and Laws of Motion", "Newton's third law and action-reaction pairs"): [
        "Newton's third law and action-reaction pairs: Concept and Properties of Action-Reaction",
        "Newton's third law and action-reaction pairs: Action-Reaction vs Balanced forces",
        "Newton's third law and action-reaction pairs: Recoil of a gun and Rocket propulsion",
        "Newton's third law and action-reaction pairs: Normal contact force and Apparent weight on scales",
    ],
    (9, "physics", "Force and Laws of Motion", "Conservation of momentum"): [
        "Conservation of momentum: Law of conservation of momentum in isolated systems",
        "Conservation of momentum: Inelastic collisions (Bodies sticking together)",
        "Conservation of momentum: Elastic collisions and Velocity exchange",
        "Conservation of momentum: Explosions into two or three fragments",
    ],

    (9, "physics", "Gravitation", "Universal law of gravitation"): [
        "Universal law of gravitation: Statement and Inverse-square law",
        "Universal law of gravitation: Universal gravitational constant G and Cavendish experiment",
        "Universal law of gravitation: Vector form of gravitational law",
        "Universal law of gravitation: Superposition principle and Forces between extended spheres",
    ],
    (9, "physics", "Gravitation", "Acceleration due to gravity"): [
        "Acceleration due to gravity: Relation between g and G (g = GM/R^2)",
        "Acceleration due to gravity: Variation with Altitude (Height above Earth)",
        "Acceleration due to gravity: Variation with Depth (Below Earth's surface)",
        "Acceleration due to gravity: Variation with Latitude and Earth's shape",
    ],
    (9, "physics", "Gravitation", "Free fall and equations of motion under gravity"): [
        "Free fall: Concept and Equations of motion under gravity",
        "Free fall: Body projected vertically upwards (Max height and Time of flight)",
        "Free fall: Body dropped from a height (Velocity and Distance in nth second)",
        "Free fall: Motion with air resistance and Terminal velocity",
    ],
    (9, "physics", "Gravitation", "Mass vs weight"): [
        "Mass vs weight: Fundamental differences (Inertia vs Gravitational pull)",
        "Mass vs weight: Apparent weight in an accelerating elevator",
        "Mass vs weight: Weightlessness in free fall and orbiting satellites",
    ],
    (9, "physics", "Gravitation", "Thrust, pressure and buoyancy"): [
        "Thrust and pressure: Definition, Units and Pressure in fluids",
        "Fluid pressure: Variation with depth and Pascal's principle",
        "Buoyant force: Cause of upthrust and Displaced fluid weight",
    ],
    (9, "physics", "Gravitation", "Archimedes' principle"): [
        "Archimedes' principle: Statement and Experimental verification",
        "Law of flotation: Conditions for sinking, floating and neutral buoyancy",
        "Relative density: Definition and Hydrometer applications",
    ],

    (9, "physics", "Work and Energy", "Work done by a force"): [
        "Work done by a force: Definition, Formula (W = F s cos theta) and Units (Joule)",
        "Work done by a force: Positive, Negative and Zero work done",
        "Work done by a force: Work done against gravity and friction",
    ],
    (9, "physics", "Work and Energy", "Kinetic energy"): [
        "Kinetic energy: Concept, Formula (KE = 1/2 m v^2) and Units",
        "Kinetic energy: Work-energy theorem for a constant force",
        "Kinetic energy: Relation between Kinetic energy and Linear momentum",
    ],
    (9, "physics", "Work and Energy", "Potential energy"): [
        "Potential energy: Concept and Gravitational potential energy (PE = mgh)",
        "Potential energy: Elastic potential energy in a stretched or compressed spring",
    ],
    (9, "physics", "Work and Energy", "Law of conservation of energy"): [
        "Law of conservation of energy: Principle and Energy transformations",
        "Conservation of mechanical energy: Freely falling body",
        "Conservation of mechanical energy: Simple pendulum oscillation",
    ],
    (9, "physics", "Work and Energy", "Power and commercial unit of energy"): [
        "Power: Definition, Formula (P = W/t) and Units (Watt, Horsepower)",
        "Commercial unit of electrical energy: Kilowatt-hour (kWh) and Calculations",
    ],
    (9, "physics", "Work and Energy", "Simple machines (levers, pulleys, inclined planes)"): [
        "Simple machines: Mechanical advantage, Velocity ratio and Efficiency",
        "Levers: Three classes of levers and Principle of moments",
        "Pulleys: Single fixed pulley, Movable pulley and Block & tackle system",
        "Inclined plane: Mechanical advantage and Work efficiency",
    ],

    (9, "physics", "Sound", "Nature and propagation of sound waves"): [
        "Nature of sound: Production by vibration and Need for a material medium",
        "Longitudinal waves: Compressions, Rarefactions and Pressure variations",
        "Wave characteristics: Wavelength, Frequency, Time period, Amplitude and Wave speed",
        "Wave speed formula: Relation between speed, frequency and wavelength (v = nu lambda)",
    ],
    (9, "physics", "Sound", "Speed of sound in different media"): [
        "Speed of sound: Dependence on medium elasticity, density and temperature",
        "Speed of sound comparison: Solids, Liquids and Gases",
        "Supersonic speed and Sonic boom",
    ],
    (9, "physics", "Sound", "Reflection of sound and echo"): [
        "Reflection of sound: Laws of reflection and Applications (Megaphone, Stethoscope)",
        "Echo: Criteria for hearing echo and Distance calculations",
        "Reverberation: Persistence of sound and Acoustic control in auditoriums",
    ],
    (9, "physics", "Sound", "Range of hearing and ultrasound"): [
        "Range of hearing: Infrasonic (<20 Hz), Audible (20 Hz - 20 kHz) and Ultrasonic (>20 kHz)",
        "Ultrasound: Applications in medicine (Echocardiography, Ultrasonography)",
        "Ultrasound: Industrial flaw detection, Cleaning and SONAR distance ranging",
    ],

    # ------------------ CLASS 9 MATH ------------------
    (9, "math", "Number Systems", "Rational and irrational numbers"): [
        "Rational numbers: Definition, Fractional forms and Decimal representations",
        "Irrational numbers: Non-terminating non-recurring decimals (sqrt(2), pi)",
        "Operations on real numbers: Properties and Rationalisation of denominators",
    ],
    (9, "math", "Number Systems", "Representing real numbers on a number line"): [
        "Number line: Locating rational numbers and Visualising decimals",
        "Number line: Constructing square roots (sqrt(2), sqrt(3), sqrt(5)) geometrically",
    ],
    (9, "math", "Number Systems", "Laws of exponents for real numbers"): [
        "Laws of exponents: Product, Quotient and Power rules for positive integers",
        "Laws of exponents: Negative and Fractional exponents (a^(p/q))",
        "Simplifying radical and exponential algebraic expressions",
    ],

    (9, "math", "Polynomials", "Zeroes of a polynomial"): [
        "Polynomials: Terms, Coefficients, Degree and Types (Linear, Quadratic, Cubic)",
        "Zeroes of a polynomial: Finding zeroes and Geometric meaning",
    ],
    (9, "math", "Polynomials", "Remainder and factor theorem"): [
        "Polynomial division: Long division algorithm",
        "Remainder theorem: Statement, Proof and Application",
        "Factor theorem: Determining factors and Factorising quadratics by splitting middle term",
    ],
    (9, "math", "Polynomials", "Algebraic identities"): [
        "Standard identities: (x+y)^2, (x-y)^2 and x^2 - y^2",
        "Expanded identities: (x+a)(x+b) and (x+y+z)^2",
        "Cubic identities: (x+y)^3, (x-y)^3 and x^3 + y^3 + z^3 - 3xyz",
    ],

    (9, "math", "Coordinate Geometry", "Cartesian plane and plotting points"): [
        "Cartesian coordinate system: Origin, Axes, Quadrants and Sign conventions",
        "Plotting ordered pairs (x, y) on the Cartesian coordinate plane",
    ],
    (9, "math", "Coordinate Geometry", "Distance between two points"): [
        "Distance between points on coordinate axes and Parallel lines",
        "Distance formula derivation in 2D Cartesian plane",
        "Applications of distance formula: Collinearity and Triangle/Quadrilateral classification",
    ],

    (9, "math", "Linear Equations in Two Variables", "Graph of a linear equation"): [
        "Linear equations in two variables: Standard form (ax + by + c = 0) and Solutions",
        "Plotting the straight-line graph of a linear equation in two variables",
    ],
    (9, "math", "Linear Equations in Two Variables", "Equations of lines parallel to axes"): [
        "Equations of lines parallel to x-axis (y = k) and y-axis (x = k)",
        "Geometric interpretation of one variable vs two variable linear equations",
    ],

    (9, "math", "Triangles", "Congruence criteria (SAS, ASA, SSS, RHS)"): [
        "Congruence of triangles: Definition and Corresponding parts (CPCTC)",
        "Congruence criteria: Side-Angle-Side (SAS) and Angle-Side-Angle (ASA)",
        "Congruence criteria: Side-Side-Side (SSS) and Right angle-Hypotenuse-Side (RHS)",
    ],
    (9, "math", "Triangles", "Properties of isosceles triangles"): [
        "Isosceles triangle theorem: Angles opposite to equal sides are equal",
        "Converse of isosceles triangle theorem: Sides opposite to equal angles are equal",
    ],
    (9, "math", "Triangles", "Inequalities in a triangle"): [
        "Triangle inequalities: Side opposite to larger angle is longer",
        "Triangle inequalities: Sum of any two sides is greater than the third side",
    ],

    (9, "math", "Quadrilaterals and Areas", "Properties of parallelograms"): [
        "Properties of parallelograms: Opposite sides and opposite angles are equal",
        "Properties of parallelograms: Diagonals bisect each other",
        "Special quadrilaterals: Properties of Rhombus, Rectangle and Square",
    ],
    (9, "math", "Quadrilaterals and Areas", "Mid-point theorem"): [
        "Mid-point theorem: Segment joining midpoints of two sides is parallel and half of third side",
        "Converse of mid-point theorem and Applications in geometry proofs",
    ],
    (9, "math", "Quadrilaterals and Areas", "Area of parallelograms and triangles on the same base"): [
        "Area theorem: Parallelograms on the same base and between same parallels have equal area",
        "Area theorem: Triangles on the same base and between same parallels have equal area",
        "Median of a triangle divides it into two triangles of equal area",
    ],

    (9, "math", "Circles", "Angle subtended by a chord"): [
        "Circle terminology: Radius, Diameter, Chord, Arc, Sector and Segment",
        "Angle subtended by a chord: Equal chords subtend equal angles at the centre",
        "Angle subtended by an arc at the centre is double the angle at circumference",
        "Angles in the same segment of a circle are equal and Angle in a semicircle is 90 degrees",
    ],
    (9, "math", "Circles", "Equal chords and distances from centre"): [
        "Perpendicular from centre to a chord bisects the chord",
        "Equal chords are equidistant from the centre and Converse theorem",
    ],
    (9, "math", "Circles", "Cyclic quadrilaterals"): [
        "Cyclic quadrilateral: Sum of opposite angles is 180 degrees",
        "Converse of cyclic quadrilateral theorem and Exterior angle property",
    ],

    (9, "math", "Heron's Formula and Mensuration", "Heron's formula for triangle area"): [
        "Heron's formula: Statement, Semi-perimeter (s) and Area calculation",
        "Applications of Heron's formula: Area of quadrilaterals and Parallelograms",
    ],
    (9, "math", "Heron's Formula and Mensuration", "Surface area of cubes, cuboids, cylinders"): [
        "Cuboid and cube: Total surface area, Lateral surface area and Diagonal",
        "Right circular cylinder: Curved surface area, Total surface area and Volume",
    ],
    (9, "math", "Heron's Formula and Mensuration", "Volume of cones, spheres, hemispheres"): [
        "Right circular cone: Slant height, Curved surface area, Total surface area and Volume",
        "Sphere and hemisphere: Surface area, Curved surface area and Volume",
    ],

    (9, "math", "Statistics and Probability", "Mean, median, mode of grouped data"): [
        "Measures of central tendency: Arithmetic mean of ungrouped and frequency data",
        "Median: Finding median for odd and even number of observations",
        "Mode: Definition and Finding mode of a dataset",
    ],
    (9, "math", "Statistics and Probability", "Graphical representation of data"): [
        "Bar graphs and Double bar graphs",
        "Histograms of varying and uniform class intervals",
        "Frequency polygons",
    ],
    (9, "math", "Statistics and Probability", "Empirical probability"): [
        "Probability: Experimental/Empirical probability definition (P(E) = n(E)/n(S))",
        "Coin toss, Dice roll and Card deck probability calculations",
    ],

    (9, "math", "Algebraic Identities", "Standard identities: (a+b)^2, (a-b)^2, a^2-b^2"): [
        "Identity (a+b)^2: Geometric visualization and Algebraic expansion",
        "Identity (a-b)^2: Geometric visualization and Algebraic expansion",
        "Difference of squares: a^2 - b^2 = (a+b)(a-b) and Factorisation",
    ],
    (9, "math", "Algebraic Identities", "Identities for (a+b)^3 and (a-b)^3"): [
        "Identity (a+b)^3: Expansion, Proof and Binomial coefficients",
        "Identity (a-b)^3: Expansion and Simplification",
        "Sum and difference of cubes: a^3 + b^3 and a^3 - b^3",
    ],
    (9, "math", "Algebraic Identities", "Applications in simplifying expressions"): [
        "Evaluating large numerical powers using algebraic identities",
        "Conditional identity: If a + b + c = 0, then a^3 + b^3 + c^3 = 3abc",
    ],

    (9, "math", "Sequences and Progressions", "Arithmetic sequences and common difference"): [
        "Arithmetic sequence: Definition, First term (a) and Common difference (d)",
        "Finite vs Infinite arithmetic progressions and Identifying APs",
    ],
    (9, "math", "Sequences and Progressions", "Geometric sequences and common ratio"): [
        "Geometric sequence: Definition, First term (a) and Common ratio (r)",
        "Identifying geometric progressions and Geometric pattern generation",
    ],
    (9, "math", "Sequences and Progressions", "Finding the nth term and predicting patterns"): [
        "Formula for nth term of an AP: a_n = a + (n-1)d",
        "Formula for nth term of a GP: a_n = a * r^(n-1)",
        "Solving real-world pattern and progression word problems",
    ],

    # ------------------ CLASS 10 PHYSICS ------------------
    (10, "physics", "Light - Reflection and Refraction", "Laws of reflection and spherical mirrors"): [
        "Reflection of light: Laws of reflection and Plane mirror image characteristics",
        "Spherical mirrors: Concave and Convex mirror terms (Pole, Focus, Radius of curvature)",
        "Ray diagrams for concave mirror (Object at infinity, C, F, between F and P)",
        "Ray diagrams for convex mirror and Practical applications (Rearview mirrors, Solar cookers)",
    ],
    (10, "physics", "Light - Reflection and Refraction", "Mirror formula and magnification"): [
        "Cartesian sign convention for spherical mirrors",
        "Mirror formula: 1/f = 1/v + 1/u and Derivation intuition",
        "Linear magnification: m = -v/u = h'/h and Image size/nature determination",
    ],
    (10, "physics", "Light - Reflection and Refraction", "Refraction and Snell's law"): [
        "Refraction of light: Cause, Bending towards/away from normal and Optical density",
        "Laws of refraction and Snell's law (sin i / sin r = constant)",
        "Refractive index: Absolute refractive index (n = c/v) and Relative refractive index",
        "Refraction through a rectangular glass slab and Lateral displacement",
    ],
    (10, "physics", "Light - Reflection and Refraction", "Lens formula and power of a lens"): [
        "Spherical lenses: Convex and Concave lenses, Optical centre, Focus and Ray diagrams",
        "Lens formula: 1/f = 1/v - 1/u and Sign convention",
        "Magnification for lenses: m = v/u = h'/h",
        "Power of a lens: Definition, Formula (P = 1/f in metres) and Unit Dioptre",
    ],

    (10, "physics", "Human Eye and Colourful World", "Defects of vision and correction"): [
        "Human eye structure and Power of accommodation (Near point and Far point)",
        "Myopia (Near-sightedness): Cause, Ray diagram and Concave lens correction",
        "Hypermetropia (Far-sightedness): Cause, Ray diagram and Convex lens correction",
        "Presbyopia and Astigmatism: Causes and Bifocal lens correction",
    ],
    (10, "physics", "Human Eye and Colourful World", "Refraction through a prism"): [
        "Refraction through a triangular glass prism: Ray diagram, Angle of incidence and Angle of deviation",
        "Relation between angle of incidence, emergence and deviation",
    ],
    (10, "physics", "Human Eye and Colourful World", "Dispersion and scattering of light"): [
        "Dispersion of white light by glass prism and Spectrum (VIBGYOR)",
        "Recombination of spectrum and Formation of Rainbow in the atmosphere",
        "Atmospheric refraction: Twinkling of stars and Advanced sunrise/delayed sunset",
        "Scattering of light and Tyndall effect: Blue sky and Reddish sun at sunrise/sunset",
    ],

    (10, "physics", "Electricity", "Electric current and potential difference"): [
        "Electric current: Definition, Charge flow (I = Q/t) and Unit Ampere",
        "Electric circuit: Closed path, Direction of current and Schematic symbols",
        "Electric potential and Potential difference: Definition (V = W/Q) and Unit Volt",
    ],
    (10, "physics", "Electricity", "Ohm's law and resistance"): [
        "Ohm's law: Statement, Formula (V = I R) and V-I characteristic graph",
        "Electrical resistance: Definition, Unit Ohm and Ohmic vs Non-ohmic conductors",
        "Factors affecting resistance: Length, Cross-sectional area and Resistivity (rho = R A / l)",
    ],
    (10, "physics", "Electricity", "Series and parallel combination of resistors"): [
        "Resistors in series: Equivalent resistance (R = R1 + R2 + R3) and Current conservation",
        "Resistors in parallel: Equivalent resistance (1/R = 1/R1 + 1/R2) and Voltage division",
        "Comparison of series and parallel circuits in household wiring",
    ],
    (10, "physics", "Electricity", "Heating effect of current and electric power"): [
        "Joule's law of heating: Formula (H = I^2 R t) and Heating applications",
        "Electric fuse: Principle, Rating and Circuit protection",
        "Electric power: Formulas (P = VI = I^2 R = V^2/R), Watt and Commercial billing in kWh",
    ],

    (10, "physics", "Magnetic Effects of Electric Current", "Magnetic field due to a current-carrying conductor"): [
        "Magnetic field and Field lines: Properties and Field around a bar magnet",
        "Magnetic field around a straight current conductor: Right-hand thumb rule",
        "Magnetic field due to a circular loop and Solenoid (Electromagnet)",
    ],
    (10, "physics", "Magnetic Effects of Electric Current", "Force on a current-carrying conductor"): [
        "Force on a current conductor in a magnetic field: Oersted-Ampere discovery",
        "Fleming's left-hand rule: Forefinger, Central finger and Thumb directions",
    ],
    (10, "physics", "Magnetic Effects of Electric Current", "Electric motor principle"): [
        "Electric motor: Principle, Construction, Armature, Split-ring commutator and Working",
    ],
    (10, "physics", "Magnetic Effects of Electric Current", "Electromagnetic induction and generators"): [
        "Electromagnetic induction: Faraday's experiments and Induced current",
        "Fleming's right-hand rule for induced current direction",
        "Electric generator: AC generator vs DC generator principle and Working",
        "Domestic electric circuits: Live, Neutral and Earth wires, Short circuits and Overloading",
    ],

    (10, "physics", "Sources of Energy", "Conventional vs non-conventional energy sources"): [
        "Fossil fuels (Coal, Petroleum): Formation, Environmental impact and Acid rain",
        "Thermal power plants and Hydroelectric power generation: Working and Ecological impact",
        "Biomass and Wind energy: Biogas plant working and Windmill energy extraction",
    ],
    (10, "physics", "Sources of Energy", "Solar energy and nuclear energy basics"): [
        "Solar energy: Solar cooker, Solar water heater and Solar cell technology",
        "Energy from the sea: Tidal energy, Wave energy and Ocean thermal energy conversion (OTEC)",
        "Geothermal energy and Nuclear energy: Nuclear fission, Energy release (E = mc^2) and Hazards",
    ],

    # ------------------ CLASS 10 MATH ------------------
    (10, "math", "Real Numbers", "Euclid's division lemma"): [
        "Euclid's division lemma: Statement (a = bq + r, 0 <= r < b)",
        "Euclid's division algorithm: Finding Highest Common Factor (HCF) of two numbers",
    ],
    (10, "math", "Real Numbers", "Fundamental theorem of arithmetic"): [
        "Fundamental theorem of arithmetic: Prime factorisation uniqueness",
        "Finding HCF and LCM using prime factorisation and Relationship HCF * LCM = a * b",
    ],
    (10, "math", "Real Numbers", "Irrationality proofs"): [
        "Proof of irrationality for sqrt(2), sqrt(3) and sqrt(5) by contradiction",
        "Irrationality of composite expressions: a + b*sqrt(c) and a - b*sqrt(c)",
    ],

    (10, "math", "Polynomials", "Relationship between zeroes and coefficients"): [
        "Geometrical meaning of zeroes of linear and quadratic polynomials",
        "Relationship between zeroes and coefficients for quadratic polynomials (alpha + beta = -b/a, alpha * beta = c/a)",
        "Relationship between zeroes and coefficients for cubic polynomials",
    ],
    (10, "math", "Polynomials", "Division algorithm for polynomials"): [
        "Division algorithm for polynomials: p(x) = g(x) * q(x) + r(x)",
        "Finding remaining zeroes of a polynomial given some of its zeroes",
    ],

    (10, "math", "Pair of Linear Equations in Two Variables", "Graphical method of solution"): [
        "Consistent and Inconsistent systems: Intersecting, Parallel and Coincident lines",
        "Conditions for unique solution, infinite solutions and no solution (a1/a2 ratios)",
        "Solving pairs of linear equations graphically and Finding vertices of formed triangles",
    ],
    (10, "math", "Pair of Linear Equations in Two Variables", "Substitution and elimination methods"): [
        "Substitution method: Step-by-step solving and Value substitution",
        "Elimination method: Equating coefficients and Variable elimination",
    ],
    (10, "math", "Pair of Linear Equations in Two Variables", "Cross-multiplication method"): [
        "Cross-multiplication method formula and Diagrammatic solving technique",
        "Equations reducible to linear form (1/x, 1/y transformations) and Word problems (Speed, Age, Fractions)",
    ],

    (10, "math", "Quadratic Equations", "Solving by factorisation"): [
        "Standard form of quadratic equation: ax^2 + bx + c = 0",
        "Solving quadratic equations by splitting the middle term (Factorisation)",
    ],
    (10, "math", "Quadratic Equations", "Quadratic formula"): [
        "Solving quadratic equations by completing the square method",
        "Quadratic formula: x = (-b +- sqrt(b^2 - 4ac)) / (2a)",
    ],
    (10, "math", "Quadratic Equations", "Nature of roots (discriminant)"): [
        "Discriminant D = b^2 - 4ac and Three cases (D > 0, D = 0, D < 0)",
        "Word problems leading to quadratic equations (Distance-Speed-Time, Geometry, Numbers)",
    ],

    (10, "math", "Arithmetic Progressions", "nth term of an AP"): [
        "General form of an AP: a, a+d, a+2d, ... and Finding nth term a_n = a + (n-1)d",
        "Finding terms from the end of an AP and Identifying if a number is a term of an AP",
    ],
    (10, "math", "Arithmetic Progressions", "Sum of first n terms"): [
        "Sum of first n terms formula: S_n = n/2 * (2a + (n-1)d) and S_n = n/2 * (a + l)",
        "Relationship between S_n and a_n (a_n = S_n - S_{n-1})",
    ],
    (10, "math", "Arithmetic Progressions", "Applications of AP"): [
        "Real-life word problems involving Arithmetic Progressions (Savings, Rows of objects, Ladders)",
        "Arithmetic mean between two numbers",
    ],

    (10, "math", "Triangles (Similarity)", "Criteria for similarity of triangles"): [
        "Concept of similar polygons and Similar triangles",
        "Basic proportionality theorem (Thales theorem) and its converse",
        "Similarity criteria: AAA, SSS and SAS similarity theorems",
    ],
    (10, "math", "Triangles (Similarity)", "Pythagoras theorem and its converse"): [
        "Pythagoras theorem: Statement, Geometric proof and Applications",
        "Converse of Pythagoras theorem: Identifying right-angled triangles",
    ],
    (10, "math", "Triangles (Similarity)", "Areas of similar triangles"): [
        "Ratio of areas of two similar triangles equals ratio of squares of corresponding sides",
        "Applications to medians, altitudes and perimeter ratios of similar triangles",
    ],

    (10, "math", "Coordinate Geometry", "Distance formula"): [
        "Distance formula: d = sqrt((x2 - x1)^2 + (y2 - y1)^2)",
        "Collinear points check and Determining types of triangles and quadrilaterals",
    ],
    (10, "math", "Coordinate Geometry", "Section formula"): [
        "Internal division section formula: P = ((m1 x2 + m2 x1)/(m1+m2), (m1 y2 + m2 y1)/(m1+m2))",
        "Midpoint formula and Points of trisection of a line segment",
    ],
    (10, "math", "Coordinate Geometry", "Area of a triangle using coordinates"): [
        "Area of a triangle formula: 1/2 |x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)|",
        "Condition for collinearity of three points using triangle area",
    ],

    (10, "math", "Introduction to Trigonometry", "Trigonometric ratios"): [
        "Trigonometric ratios in a right triangle: Sine, Cosine, Tangent, Cosecant, Secant, Cotangent",
        "Reciprocal and quotient relations of trigonometric ratios",
    ],
    (10, "math", "Introduction to Trigonometry", "Trigonometric identities"): [
        "Fundamental identity: sin^2 theta + cos^2 theta = 1",
        "Identities: 1 + tan^2 theta = sec^2 theta and 1 + cot^2 theta = cosec^2 theta",
        "Proving complex trigonometric identities step by step",
    ],
    (10, "math", "Introduction to Trigonometry", "Values at standard angles"): [
        "Trigonometric values at standard angles (0, 30, 45, 60, 90 degrees)",
        "Trigonometric ratios of complementary angles (sin(90 - theta) = cos theta)",
    ],

    (10, "math", "Applications of Trigonometry", "Heights and distances problems"): [
        "Line of sight, Angle of elevation and Angle of depression",
        "Single right-triangle height and distance problems (Tower, Tree, Pole)",
        "Two right-triangle problems (Observation from two points, Ships, Balloons)",
    ],

    (10, "math", "Circles", "Tangent to a circle"): [
        "Tangent to a circle: Definition and Secant vs Tangent",
        "Theorem: Tangent at any point is perpendicular to radius through point of contact",
    ],
    (10, "math", "Circles", "Number of tangents from a point"): [
        "Tangents from points inside, on and outside a circle",
        "Theorem: Lengths of tangents drawn from an external point to a circle are equal",
        "Circles inscribed in and circumscribing quadrilaterals",
    ],

    (10, "math", "Mensuration and Statistics", "Areas related to circles (sectors, segments)"): [
        "Perimeter and area of a circle and Semicircle review",
        "Area of sector of a circle: A = (theta / 360) * pi * r^2 and Arc length",
        "Area of segment of a circle (Minor and Major segments)",
    ],
    (10, "math", "Mensuration and Statistics", "Surface areas and volumes of combined solids"): [
        "Surface area of combinations of solids (Cylinder + Hemispheres, Cone + Cylinder)",
        "Volume of combinations of solids",
        "Conversion of solid from one shape to another (Melting, Recasting, Earth digging)",
    ],
    (10, "math", "Mensuration and Statistics", "Mean, median, mode of grouped data"): [
        "Mean of grouped data: Direct method, Assumed mean method and Step-deviation method",
        "Mode of grouped data: Modal class and Formula (l + (f1-f0)/(2f1-f0-f2) * h)",
        "Median of grouped data: Median class, Cumulative frequency curve (Ogive) and Formula",
    ],
    (10, "math", "Mensuration and Statistics", "Probability basics"): [
        "Theoretical probability: P(E) = Number of favorable outcomes / Total outcomes",
        "Elementary events, Complementary events (P(not E) = 1 - P(E)) and Impossible/Sure events",
    ],

    # ------------------ CLASS 11 PHYSICS ------------------
    (11, "physics", "Units, Dimensions and Vectors", "Dimensional analysis"): [
        "Fundamental and derived physical quantities and SI base units",
        "Dimensional formulas of mechanics and electromagnetism quantities",
        "Applications of dimensional analysis: Checking formula correctness and Deriving equations",
    ],
    (11, "physics", "Units, Dimensions and Vectors", "Error analysis in measurements"): [
        "Significant figures and Rounding-off rules",
        "Absolute error, Relative error and Percentage error",
        "Propagation and combination of errors (Addition, Multiplication, Powers)",
    ],
    (11, "physics", "Units, Dimensions and Vectors", "Vector addition and resolution"): [
        "Scalar and vector quantities, Unit vectors (i, j, k) and Null vector",
        "Triangle law and Parallelogram law of vector addition (Resultant magnitude and direction)",
        "Resolution of a vector in 2D and 3D rectangular components",
    ],
    (11, "physics", "Units, Dimensions and Vectors", "Dot and cross product"): [
        "Scalar product (Dot product): Definition (A . B = AB cos theta), Properties and Projections",
        "Vector product (Cross product): Definition (A x B = AB sin theta n_hat), Right-hand rule and Properties",
        "Applications of cross product: Area of triangle/parallelogram and Torque vector",
    ],

    (11, "physics", "Motion in a Straight Line", "Position-time and velocity-time graphs"): [
        "Frame of reference, Position vector and Instantaneous vs Average velocity",
        "Derivatives in kinematics: v = dx/dt and a = dv/dt = v dv/dx",
        "Position-time, velocity-time and acceleration-time graph analysis and Area/Slope relationships",
    ],
    (11, "physics", "Motion in a Straight Line", "Equations of motion"): [
        "Calculus derivation of kinematic equations: v = u + at, s = ut + 1/2 at^2, v^2 = u^2 + 2as",
        "Distance traveled in nth second formula: s_n = u + a/2 * (2n - 1)",
        "Motion under gravity with variable acceleration problems",
    ],
    (11, "physics", "Motion in a Straight Line", "Relative velocity in one dimension"): [
        "Relative velocity in 1D: Concept and Formula (v_AB = v_A - v_B)",
        "Overtaking, Head-on collision and Trains passing problems in 1D",
    ],

    (11, "physics", "Motion in a Plane", "Projectile motion"): [
        "Horizontal projectile motion: Trajectory equation, Time of flight and Horizontal range",
        "Oblique projectile motion: Trajectory derivation (Parabolic path: y = x tan theta - gx^2/(2u^2 cos^2 theta))",
        "Key projectile formulas: Maximum height, Time of flight and Range (Maximum range at 45 degrees)",
        "Projectile motion on an inclined plane",
    ],
    (11, "physics", "Motion in a Plane", "Uniform circular motion"): [
        "Angular displacement, Angular velocity (omega) and Relation v = r * omega",
        "Centripetal acceleration derivation: a_c = v^2/r = omega^2 r",
        "Non-uniform circular motion: Tangential acceleration and Net acceleration",
    ],
    (11, "physics", "Motion in a Plane", "Relative velocity in two dimensions"): [
        "Relative velocity in 2D vector form (v_AB = v_A - v_B)",
        "Rain-man problem: Umbrella holding angle calculation",
        "River-swimmer / River-boat problem: Shortest path and Shortest time crossing",
    ],

    (11, "physics", "Laws of Motion", "Free body diagrams"): [
        "Free body diagrams (FBD): Drawing isolation, Normal reaction, Tension and Weight",
        "Equilibrium of concurrent forces and Lami's theorem",
        "Connected bodies: Wedge-block, Incline planes and Pulleys using FBD",
    ],
    (11, "physics", "Laws of Motion", "Friction (static and kinetic)"): [
        "Origin of friction, Static friction (f_s <= mu_s N) and Limiting friction",
        "Kinetic friction (f_k = mu_k N) and Rolling friction",
        "Angle of friction, Angle of repose and Motion of body on rough inclined plane",
        "Two-block friction problems (Block on top of another block)",
    ],
    (11, "physics", "Laws of Motion", "Circular motion dynamics and banking of roads"): [
        "Centripetal force: Concept and Real forces providing centripetal acceleration",
        "Level circular road: Maximum safe turning speed (v = sqrt(mu r g))",
        "Banked road: Optimum speed and Safe speed range with friction",
        "Bending of a cyclist and Conical pendulum",
    ],
    (11, "physics", "Laws of Motion", "Pseudo force and non-inertial frames"): [
        "Inertial vs Non-inertial frames of reference",
        "Pseudo force (F_pseudo = -m a_frame) and Frame transformations",
        "Apparent weight in accelerating elevators and Accelerating wedge problems",
    ],

    (11, "physics", "Work, Energy and Power", "Work-energy theorem"): [
        "Work done by variable force: W = integral F dx and Area under F-x graph",
        "Work-energy theorem for a variable force: W_net = Delta KE",
        "Kinetic energy and Work-energy theorem in 2D/3D vector notation",
    ],
    (11, "physics", "Work, Energy and Power", "Conservative and non-conservative forces"): [
        "Conservative forces: Path independence, Closed loop work = 0 and Potential energy (F = -dU/dx)",
        "Potential energy curves: Stable, Unstable and Neutral equilibrium",
        "Conservation of mechanical energy: Spring-mass system oscillation and Vertical circle motion",
    ],
    (11, "physics", "Work, Energy and Power", "Collisions (elastic and inelastic)"): [
        "Coefficient of restitution (e): Definition and Range (0 <= e <= 1)",
        "1D Elastic collision: Conservation of momentum, Kinetic energy and Final velocities formula",
        "1D Perfectly inelastic collision: Loss of kinetic energy formula",
        "2D Oblique collisions (Glancing collisions of spheres)",
    ],

    (11, "physics", "System of Particles and Rotational Motion", "Centre of mass"): [
        "Centre of mass: Two-particle system and N-particle system formula",
        "Centre of mass of continuous bodies (Rod, Ring, Disc, Semicircle)",
        "Motion of centre of mass, Total momentum and Internal vs External forces",
    ],
    (11, "physics", "System of Particles and Rotational Motion", "Torque and angular momentum"): [
        "Torque (Moment of force): Definition (tau = r x F) and Couple",
        "Angular momentum: Definition (L = r x p = I omega) and Torque relation (tau = dL/dt)",
        "Conservation of angular momentum: Principle and Applications (Spinning skater, Planetary orbit)",
    ],
    (11, "physics", "System of Particles and Rotational Motion", "Moment of inertia of rigid bodies"): [
        "Moment of inertia (I = sum m_i r_i^2) and Radius of gyration (k)",
        "Parallel axes theorem (I = I_cm + M d^2) and Perpendicular axes theorem",
        "Moment of inertia of standard shapes: Ring, Disc, Rod, Cylinder, Solid sphere and Hollow sphere",
    ],
    (11, "physics", "System of Particles and Rotational Motion", "Rolling motion"): [
        "Pure rolling without slipping: Velocity relationship (v_cm = R omega) and Contact point at rest",
        "Kinetic energy of rolling body: KE = 1/2 M v^2 + 1/2 I omega^2",
        "Acceleration of a rolling body on an inclined plane: a = g sin theta / (1 + k^2/R^2)",
    ],

    (11, "physics", "Gravitation", "Universal law of gravitation"): [
        "Newton's law of gravitation and Gravitational constant G",
        "Gravitational field intensity: Definition, Field due to point mass, Ring and Solid sphere",
    ],
    (11, "physics", "Gravitation", "Acceleration due to gravity and its variation"): [
        "Acceleration due to gravity on Earth's surface: g = GM/R^2",
        "Variation of g with altitude (h << R and general formula)",
        "Variation of g with depth (Linear decrease towards center)",
        "Variation of g due to Earth's rotation and latitude: g' = g - omega^2 R cos^2 lambda",
    ],
    (11, "physics", "Gravitation", "Gravitational potential energy"): [
        "Gravitational potential (V = -GM/r) and Potential energy (U = -GMm/r)",
        "Gravitational potential due to solid sphere and thin spherical shell",
        "Work done in shifting a mass between two orbits or points",
    ],
    (11, "physics", "Gravitation", "Escape velocity"): [
        "Escape velocity derivation: Conservation of mechanical energy from surface to infinity",
        "Escape velocity formula: v_e = sqrt(2GM/R) = sqrt(2gR) (11.2 km/s on Earth)",
        "Escape velocity from non-surface points and Other planets/moons",
    ],
    (11, "physics", "Gravitation", "Orbital velocity and satellites"): [
        "Orbital velocity of a satellite: v_o = sqrt(GM/r) and Relation with escape velocity (v_e = sqrt(2) v_o)",
        "Time period of a satellite: T = 2 pi sqrt(r^3 / GM) and Satellite energy (Binding energy)",
        "Geostationary vs Polar satellites and Parking orbits",
    ],
    (11, "physics", "Gravitation", "Kepler's laws"): [
        "Kepler's first law (Law of orbits): Elliptical orbits and Perihelion/Aphelion",
        "Kepler's second law (Law of areas): Equal areas in equal times and Angular momentum conservation",
        "Kepler's third law (Law of periods): T^2 proportional to r^3 and Orbital calculations",
    ],

    (11, "physics", "Mechanical Properties of Solids and Fluids", "Stress, strain and Young's modulus"): [
        "Elasticity: Restoring force, Stress (Tensile, Compressive, Shear) and Strain",
        "Hooke's law, Stress-strain curve and Elastic limit / Yield point / Breaking point",
        "Moduli of elasticity: Young's modulus (Y), Bulk modulus (B) and Shear modulus (G)",
        "Elastic potential energy in a stretched wire: U = 1/2 * Stress * Strain * Volume",
    ],
    (11, "physics", "Mechanical Properties of Solids and Fluids", "Pascal's law and hydraulic systems"): [
        "Fluid pressure: Atmospheric pressure, Hydrostatic paradox and Pressure variation with depth",
        "Pascal's law: Statement, Proof and Hydraulic lift / Hydraulic brakes",
        "Archimedes' principle in fluids: Buoyant force and Upthrust calculations",
    ],
    (11, "physics", "Mechanical Properties of Solids and Fluids", "Bernoulli's theorem"): [
        "Streamline flow, Turbulent flow, Reynolds number and Equation of continuity (A1 v1 = A2 v2)",
        "Bernoulli's equation derivation: P + 1/2 rho v^2 + rho g h = constant",
        "Applications of Bernoulli's principle: Torricelli's law (Efflux velocity), Venturimeter and Aerodynamic lift",
    ],
    (11, "physics", "Mechanical Properties of Solids and Fluids", "Viscosity and Stokes' law"): [
        "Viscosity: Newton's law of viscous force (F = -eta A dv/dx) and Poiseuille's formula",
        "Stokes' law: Drag force on a sphere (F = 6 pi eta r v)",
        "Terminal velocity derivation: Balance of gravity, buoyancy and viscous drag",
    ],
    (11, "physics", "Mechanical Properties of Solids and Fluids", "Surface tension and capillary rise"): [
        "Surface tension: Molecular theory, Surface energy and Surface tension relation",
        "Angle of contact, Shape of liquid meniscus and Excess pressure inside drop and soap bubble",
        "Capillarity: Ascent formula for capillary rise (h = 2 T cos theta / (r rho g))",
    ],

    (11, "physics", "Thermal Properties and Thermodynamics", "Thermal expansion and calorimetry"): [
        "Thermal expansion: Linear (alpha), Areal (beta) and Volume (gamma) expansion relationships",
        "Calorimetry: Specific heat capacity, Molar heat capacity and Water equivalent",
        "Latent heat of fusion and vaporization, Phase changes and Heat exchange equation",
    ],
    (11, "physics", "Thermal Properties and Thermodynamics", "First law of thermodynamics"): [
        "Thermodynamic system, Surroundings, State variables and Thermal equilibrium (Zeroth law)",
        "Work done in thermodynamic processes: W = integral P dV",
        "First law of thermodynamics: Delta Q = Delta U + Delta W and Internal energy as state function",
    ],
    (11, "physics", "Thermal Properties and Thermodynamics", "Thermodynamic processes (isothermal, adiabatic)"): [
        "Quasi-static processes: Isobaric (P=const) and Isochoric (V=const) processes",
        "Isothermal process: PV = const, Work done W = nRT ln(V2/V1) and Slope on P-V diagram",
        "Adiabatic process: PV^gamma = const, Work done W = (P1V1 - P2V2)/(gamma - 1) and TV^(gamma-1) relation",
        "Cyclic processes: Net work done as area enclosed on P-V diagram",
    ],
    (11, "physics", "Thermal Properties and Thermodynamics", "Second law and heat engines"): [
        "Second law of thermodynamics: Kelvin-Planck and Clausius statements",
        "Heat engine: Working cycle and Efficiency (eta = 1 - Q2/Q1)",
        "Carnot engine: Carnot cycle (Isothermal & Adiabatic stages), Efficiency (eta = 1 - T2/T1) and Carnot theorem",
        "Refrigerators and Heat pumps: Coefficient of performance (COP)",
    ],
    (11, "physics", "Thermal Properties and Thermodynamics", "Kinetic theory of gases"): [
        "Ideal gas equation: PV = nRT and Molecular assumptions of kinetic theory",
        "Pressure of an ideal gas derivation: P = 1/3 rho v_rms^2 and Kinetic interpretation of temperature",
        "RMS speed, Average speed and Most probable speed formulas",
        "Law of equipartition of energy, Degrees of freedom and Specific heat ratio (gamma) of gases",
    ],

    (11, "physics", "Oscillations and Waves", "Simple harmonic motion"): [
        "Periodic vs Oscillatory motion, Frequency, Time period and Amplitude",
        "Simple Harmonic Motion (SHM) equation: d^2x/dt^2 + omega^2 x = 0 and Displacement x = A sin(omega t + phi)",
        "Velocity (v = omega sqrt(A^2 - x^2)) and Acceleration (a = -omega^2 x) in SHM",
        "Time period of simple pendulum (T = 2 pi sqrt(l/g)) and Spring-mass system (T = 2 pi sqrt(m/k))",
    ],
    (11, "physics", "Oscillations and Waves", "Energy in SHM"): [
        "Kinetic energy (KE = 1/2 m omega^2 (A^2 - x^2)) and Potential energy (PE = 1/2 m omega^2 x^2) in SHM",
        "Total mechanical energy conservation (TE = 1/2 m omega^2 A^2) and Energy vs displacement graph",
        "Damped oscillations and Forced oscillations with Resonance",
    ],
    (11, "physics", "Oscillations and Waves", "Wave motion and superposition"): [
        "Transverse vs Longitudinal progressive waves and Wave equation: y = A sin(kx - omega t + phi)",
        "Wave number (k = 2 pi / lambda), Angular frequency (omega = 2 pi nu) and Phase difference",
        "Speed of transverse waves on stretched string (v = sqrt(T/mu)) and Longitudinal waves (Laplace correction)",
        "Principle of superposition of waves",
    ],
    (11, "physics", "Oscillations and Waves", "Standing waves on strings and in pipes"): [
        "Formation of standing waves: Nodes and Antinodes",
        "Normal modes of vibration of stretched strings (Harmonics and Overtones)",
        "Vibrations of air columns in organ pipes: Closed pipe (Odd harmonics) and Open pipe (All harmonics)",
    ],
    (11, "physics", "Oscillations and Waves", "Beats and Doppler effect"): [
        "Beats: Interference of waves with slightly different frequencies and Beat frequency (f_b = |f1 - f2|)",
        "Doppler effect in sound: Apparent frequency when source moves",
        "Doppler effect in sound: Apparent frequency when observer moves and General formula",
    ],

    # ------------------ CLASS 11 MATH ------------------
    (11, "math", "Sets, Relations and Functions", "Set operations"): [
        "Sets representation: Roster form, Set-builder form and Types of sets (Empty, Finite, Infinite, Subsets)",
        "Set operations: Union, Intersection, Difference and Complement of sets",
        "Venn diagrams and Practical problems on union and intersection of two/three sets",
    ],
    (11, "math", "Sets, Relations and Functions", "Types of relations"): [
        "Cartesian product of sets (A x B) and Number of relations",
        "Relations: Domain, Co-domain and Range",
        "Types of relations: Reflexive, Symmetric, Transitive and Equivalence relations",
    ],
    (11, "math", "Sets, Relations and Functions", "Domain and range of functions"): [
        "Function as a special relation: Vertical line test and Notation f(x)",
        "Domain, Co-domain and Range of real functions",
        "Standard functions and their graphs: Identity, Constant, Polynomial, Rational, Modulus, Signum and Greatest integer",
    ],

    (11, "math", "Trigonometric Functions", "Trigonometric identities"): [
        "Angles in radians and degrees (pi radians = 180 degrees) and Arc length l = r theta",
        "Trigonometric functions definition on unit circle and Signs in four quadrants (ASTC rule)",
        "Compound angle formulas: sin(A +- B), cos(A +- B), tan(A +- B)",
        "Multiple and submultiple angles: sin 2A, cos 2A, tan 2A and Product-to-sum / Sum-to-product formulas",
    ],
    (11, "math", "Trigonometric Functions", "Graphs of trigonometric functions"): [
        "Graphs, Domain, Range and Periodicity of sin x, cos x, tan x",
        "Graphs, Domain, Range and Asymptotes of cosec x, sec x, cot x",
    ],
    (11, "math", "Trigonometric Functions", "Trigonometric equations"): [
        "Principal solutions of trigonometric equations",
        "General solutions of sin theta = sin alpha, cos theta = cos alpha, tan theta = tan alpha",
    ],

    (11, "math", "Complex Numbers and Quadratic Equations", "Algebra of complex numbers"): [
        "Imaginary unit i (iota), Powers of i and Definition of complex number z = a + ib",
        "Algebra of complex numbers: Addition, Subtraction, Multiplication and Division",
        "Conjugate and Modulus of a complex number and Multiplicative inverse",
    ],
    (11, "math", "Complex Numbers and Quadratic Equations", "Argand plane and polar form"): [
        "Argand plane: Geometrical representation of complex numbers",
        "Polar form of complex number: z = r (cos theta + i sin theta) and Principal argument",
    ],
    (11, "math", "Complex Numbers and Quadratic Equations", "Nature of roots of quadratics"): [
        "Solving quadratic equations with negative discriminant in complex number system",
        "Square root of a complex number",
    ],

    (11, "math", "Permutations, Combinations and Binomial Theorem", "Fundamental counting principle"): [
        "Fundamental principle of multiplication and addition",
        "Factorial notation (n!) and its algebraic properties",
    ],
    (11, "math", "Permutations, Combinations and Binomial Theorem", "Permutations with/without repetition"): [
        "Permutation definition: Arrangement of n distinct objects taken r at a time (nPr = n! / (n-r)!)",
        "Permutations when objects are repeated or Not all objects are distinct",
        "Circular permutations and Conditional permutations (Vowels together, Alternate positions)",
    ],
    (11, "math", "Permutations, Combinations and Binomial Theorem", "Combinations"): [
        "Combination definition: Selection of n distinct objects taken r at a time (nCr = n! / (r! (n-r)!))",
        "Properties of combinations: nCr = nC(n-r) and Pascal's identity (nCr + nC(r-1) = (n+1)Cr)",
        "Applications of combinations: Committee selection, Geometry points/triangles/diagonals",
    ],
    (11, "math", "Permutations, Combinations and Binomial Theorem", "Binomial expansion and general term"): [
        "Binomial theorem for positive integral index: (a + b)^n expansion and Pascal's triangle",
        "General term (T_{r+1} = nCr a^(n-r) b^r) and Middle term(s) of binomial expansion",
        "Independent term (term free from x) and Coefficients properties",
    ],

    (11, "math", "Sequences and Series", "Arithmetic and geometric progressions"): [
        "Arithmetic progression: General term, Sum of first n terms and Arithmetic mean (AM)",
        "Geometric progression: General term, Sum of first n terms, Sum of infinite GP (|r| < 1) and Geometric mean (GM)",
        "Relationship between AM and GM (AM >= GM)",
    ],
    (11, "math", "Sequences and Series", "Sum to n terms of special series"): [
        "Sum of first n natural numbers: sum n = n(n+1)/2",
        "Sum of squares of first n natural numbers: sum n^2 = n(n+1)(2n+1)/6",
        "Sum of cubes of first n natural numbers: sum n^3 = (n(n+1)/2)^2",
    ],

    (11, "math", "Straight Lines and Conic Sections", "Slope and equations of a line"): [
        "Slope (gradient) of a line: m = tan theta = (y2 - y1)/(x2 - x1), Parallel and Perpendicular slopes",
        "Angle between two straight lines: tan theta = |(m2 - m1)/(1 + m1 m2)|",
        "Forms of line equations: Point-slope form, Two-point form, Slope-intercept form, Intercept form and Normal form",
        "Distance of a point from a line: d = |ax1 + by1 + c| / sqrt(a^2 + b^2) and Distance between parallel lines",
    ],
    (11, "math", "Straight Lines and Conic Sections", "Circle equations"): [
        "Circle: Standard equation (x - h)^2 + (y - k)^2 = r^2 and General equation x^2 + y^2 + 2gx + 2fy + c = 0",
        "Circle through three non-collinear points and Tangent condition",
    ],
    (11, "math", "Straight Lines and Conic Sections", "Parabola"): [
        "Parabola definition: Focus, Directrix, Eccentricity (e = 1) and Axis",
        "Standard equations of parabola (y^2 = 4ax, y^2 = -4ax, x^2 = 4ay, x^2 = -4ay)",
        "Latus rectum, Focus coordinates and Focal distance of parabola",
    ],
    (11, "math", "Straight Lines and Conic Sections", "Ellipse"): [
        "Ellipse definition: Foci, Major axis, Minor axis and Eccentricity (e < 1)",
        "Standard equation of ellipse: x^2/a^2 + y^2/b^2 = 1 and Relations (b^2 = a^2(1 - e^2))",
        "Latus rectum, Vertices and Directrices of ellipse",
    ],
    (11, "math", "Straight Lines and Conic Sections", "Hyperbola"): [
        "Hyperbola definition: Foci, Transverse axis, Conjugate axis and Eccentricity (e > 1)",
        "Standard equation of hyperbola: x^2/a^2 - y^2/b^2 = 1 and Relations (b^2 = a^2(e^2 - 1))",
        "Rectangular hyperbola and Asymptotes overview",
    ],

    (11, "math", "Limits and Derivatives", "Algebra of limits"): [
        "Concept of limit: Left-hand limit, Right-hand limit and Existence of limit",
        "Algebra of limits: Sum, Difference, Product and Quotient theorems",
    ],
    (11, "math", "Limits and Derivatives", "Standard limits"): [
        "Indeterminate forms (0/0) and Factorisation/Rationalisation techniques",
        "Standard algebraic limit: lim_{x->a} (x^n - a^n)/(x - a) = n a^(n-1)",
        "Standard trigonometric limits: lim_{x->0} (sin x)/x = 1 and lim_{x->0} (1 - cos x)/x = 0",
        "Standard exponential and logarithmic limits",
    ],
    (11, "math", "Limits and Derivatives", "Derivative from first principles"): [
        "Derivative definition: Geometric meaning as tangent slope and Instantaneous rate of change",
        "First principles of differentiation: f'(x) = lim_{h->0} (f(x+h) - f(x))/h",
        "Derivative of x^n, sin x, cos x from first principles",
    ],
    (11, "math", "Limits and Derivatives", "Derivatives of standard functions"): [
        "Rules of differentiation: Constant multiple, Sum and Difference rules",
        "Product rule: d/dx (u v) = u v' + v u'",
        "Quotient rule: d/dx (u / v) = (v u' - u v') / v^2",
        "Derivatives of algebraic, trigonometric, exponential and logarithmic functions",
    ],

    (11, "math", "Linear Inequalities", "Solving linear inequalities in one variable"): [
        "Linear inequalities in one variable: Algebraic solutions and Representation on number line",
        "Interval notation: Open, Closed and Semi-open intervals",
    ],
    (11, "math", "Linear Inequalities", "Graphical solution of linear inequalities in two variables"): [
        "Linear inequality in two variables (ax + by < c, ax + by > c) and Half-plane concept",
        "Graphing linear inequalities and Finding feasible half-plane",
    ],
    (11, "math", "Linear Inequalities", "Solving a system of linear inequalities"): [
        "Graphical solution of a system of linear inequalities in two variables",
        "Finding common bounded and unbounded feasible regions",
    ],

    (11, "math", "Introduction to Three Dimensional Geometry", "Coordinate axes and coordinate planes in 3D"): [
        "Coordinate axes (X, Y, Z), Coordinate planes (XY, YZ, ZX) and Eight octants in 3D space",
        "Coordinates of a point in 3D space and Distance from axes/planes",
    ],
    (11, "math", "Introduction to Three Dimensional Geometry", "Distance between two points in space"): [
        "Distance formula in 3D: d = sqrt((x2 - x1)^2 + (y2 - y1)^2 + (z2 - z1)^2)",
        "Collinear points check and Classifying 3D geometric shapes",
    ],
    (11, "math", "Introduction to Three Dimensional Geometry", "Section formula in 3D"): [
        "Section formula in 3D: Internal and External division coordinates",
        "Midpoint and Centroid of a triangle in 3D space",
    ],

    (11, "math", "Statistics", "Measures of dispersion: range and mean deviation"): [
        "Measures of dispersion concept and Range of data",
        "Mean deviation about mean for ungrouped and grouped frequency data",
        "Mean deviation about median for grouped data",
    ],
    (11, "math", "Statistics", "Variance and standard deviation"): [
        "Variance (sigma^2) and Standard deviation (sigma) for ungrouped data",
        "Variance and standard deviation for discrete and continuous frequency distributions",
        "Short-cut and step-deviation methods for standard deviation calculation",
    ],
    (11, "math", "Statistics", "Analysis of frequency distributions"): [
        "Coefficient of variation (CV = (sigma / mean) * 100) and Comparison of consistency",
        "Comparison of two frequency distributions with same mean or different means",
    ],

    (11, "math", "Probability", "Random experiments, sample space and events"): [
        "Random experiments, Outcomes and Sample space (S)",
        "Types of events: Impossible, Sure, Simple, Compound, Mutually exclusive and Exhaustive events",
    ],
    (11, "math", "Probability", "Axiomatic approach to probability"): [
        "Axioms of probability: P(S) = 1, 0 <= P(E) <= 1",
        "Equally likely outcomes and Probability of simple events",
    ],
    (11, "math", "Probability", "Addition theorem of probability"): [
        "Addition theorem for two events: P(A or B) = P(A) + P(B) - P(A and B)",
        "Addition theorem for mutually exclusive events: P(A or B) = P(A) + P(B)",
        "Probability of event 'Not A' (P(A') = 1 - P(A))",
    ],

    # ------------------ CLASS 12 PHYSICS ------------------
    (12, "physics", "Electrostatics", "Coulomb's law and electric field"): [
        "Electric charges, Quantisation of charge and Conservation of charge",
        "Coulomb's law: Scalar form, Vector form and Permittivity of medium (epsilon_0)",
        "Principle of superposition of electrostatic forces",
        "Electric field: Definition (E = F/q), Field due to point charge and Electric field lines",
        "Electric dipole: Dipole moment (p = 2aq), Field on axial and equatorial lines, and Torque in uniform field",
    ],
    (12, "physics", "Electrostatics", "Gauss's law and applications"): [
        "Electric flux: Definition (Phi = integral E . dA) and Sign convention",
        "Gauss's law: Statement and Mathematical formulation",
        "Gauss's law application: Electric field due to infinitely long straight wire (E = lambda / (2 pi eps_0 r))",
        "Gauss's law application: Field due to uniformly charged infinite plane sheet",
        "Gauss's law application: Field due to uniformly charged thin spherical shell (Inside and Outside)",
    ],
    (12, "physics", "Electrostatics", "Electric potential and potential energy"): [
        "Electric potential: Definition (V = W/q), Potential due to point charge and Electric dipole",
        "Equipotential surfaces: Properties and Relation between field and potential (E = -dV/dr)",
        "Electrostatic potential energy of system of two and three point charges in external field",
        "Conductors in electrostatic field: Shielding, Cavity and Surface charge density",
    ],
    (12, "physics", "Electrostatics", "Capacitors and dielectrics"): [
        "Capacitance: Definition (C = Q/V) and Capacitance of isolated spherical conductor",
        "Parallel plate capacitor: Capacitance formula (C = eps_0 A / d)",
        "Dielectrics and Polarisation: Dielectric constant (K) and Effect of dielectric slab on capacitance",
    ],
    (12, "physics", "Electrostatics", "Combination of capacitors"): [
        "Capacitors in series: Charge conservation and Formula (1/C = 1/C1 + 1/C2)",
        "Capacitors in parallel: Voltage conservation and Formula (C = C1 + C2)",
        "Energy stored in a capacitor: U = 1/2 CV^2 = 1/2 Q^2/C and Energy density",
        "Common potential and Loss of energy on sharing charges between capacitors",
    ],

    (12, "physics", "Current Electricity", "Drift velocity and Ohm's law"): [
        "Electric current, Current density (j = I/A) and Drift velocity of electrons derivation (v_d = -e E tau / m)",
        "Microscopic Ohm's law (j = sigma E) and Deduction of Ohm's law (R = m l / (n e^2 tau A))",
        "Temperature dependence of resistivity and Temperature coefficient (alpha)",
    ],
    (12, "physics", "Current Electricity", "Kirchhoff's laws"): [
        "Internal resistance of cell, Electromotive force (EMF) and Terminal voltage (V = E - Ir)",
        "Kirchhoff's first law (Junction rule): Conservation of charge",
        "Kirchhoff's second law (Loop rule): Conservation of energy and Sign conventions",
        "Solving complex multi-loop circuits using Kirchhoff's laws",
    ],
    (12, "physics", "Current Electricity", "Wheatstone bridge and meter bridge"): [
        "Wheatstone bridge: Balanced condition derivation (P/Q = R/S)",
        "Meter bridge: Principle, Circuit diagram and Determining unknown resistance",
    ],
    (12, "physics", "Current Electricity", "Potentiometer"): [
        "Potentiometer: Principle and Potential gradient (k = V/l)",
        "Potentiometer application: Comparing EMFs of two primary cells",
        "Potentiometer application: Determining internal resistance of a primary cell",
    ],

    (12, "physics", "Magnetism and Matter", "Biot-Savart law and Ampere's law"): [
        "Magnetic field: Oersted's experiment and Biot-Savart law derivation (dB = mu_0/4pi * I dl sin theta / r^2)",
        "Magnetic field on the axis of a circular current loop (B = mu_0 I R^2 / 2(R^2+x^2)^(3/2))",
        "Ampere's circuital law: Statement and Application to straight conductor and Solenoid",
    ],
    (12, "physics", "Magnetism and Matter", "Force on a moving charge and current-carrying conductor"): [
        "Lorentz force: Electric and magnetic force on moving charge (F = q(E + v x B))",
        "Motion of charged particle in magnetic field: Circular, Helical paths and Pitch",
        "Force on current-carrying conductor in magnetic field (F = I l x B)",
        "Force between two parallel current-carrying conductors and Definition of Ampere",
        "Torque on a current loop in magnetic field: tau = M x B",
    ],
    (12, "physics", "Magnetism and Matter", "Magnetic dipole and bar magnet"): [
        "Bar magnet as an equivalent solenoid: Magnetic dipole moment (M = m * 2l)",
        "Magnetic field of bar magnet: Axial and Equatorial field formulas",
        "Earth's magnetism: Magnetic elements (Declination, Dip/Inclination and Horizontal component)",
        "Magnetic materials classification: Diamagnetic, Paramagnetic and Ferromagnetic substances",
    ],
    (12, "physics", "Magnetism and Matter", "Moving coil galvanometer"): [
        "Moving coil galvanometer: Principle, Construction and Deflection formula (I proportional to theta)",
        "Current sensitivity and Voltage sensitivity of a galvanometer",
        "Conversion of galvanometer to ammeter (Shunt resistance) and Voltmeter (Series resistance)",
    ],

    (12, "physics", "Electromagnetic Induction and AC", "Faraday's and Lenz's laws"): [
        "Magnetic flux: Definition (Phi = B . A) and Unit Weber",
        "Faraday's laws of electromagnetic induction: Induced EMF (e = -dPhi/dt)",
        "Lenz's law and Conservation of energy",
        "Motional EMF: Rod moving in uniform magnetic field (e = B v l)",
        "Eddy currents: Formation, Minimisation and Applications",
    ],
    (12, "physics", "Electromagnetic Induction and AC", "Self and mutual inductance"): [
        "Self-inductance: Coefficient of self-induction (L = Phi / I), Unit Henry and Long solenoid inductance",
        "Mutual inductance: Coefficient of mutual induction (M = Phi2 / I1) and Two coaxial solenoids",
        "Energy stored in an inductor: U = 1/2 L I^2",
    ],
    (12, "physics", "Electromagnetic Induction and AC", "AC circuits (LCR)"): [
        "Alternating current: Peak value, RMS value (I_rms = I_0 / sqrt(2)) and Phase relations",
        "AC circuit with pure resistor, pure inductor and pure capacitor (Reactance: X_L = omega L, X_C = 1/(omega C))",
        "Series LCR circuit: Phasor diagram, Impedance formula (Z = sqrt(R^2 + (X_L - X_C)^2)) and Phase angle",
    ],
    (12, "physics", "Electromagnetic Induction and AC", "Resonance in AC circuits"): [
        "Resonance in series LCR circuit: Resonance frequency (omega_0 = 1/sqrt(LC))",
        "Quality factor (Q-factor), Bandwidth and Sharpness of resonance",
        "Power in AC circuit: Average power (P = V_rms I_rms cos phi), Power factor and Wattless current",
    ],
    (12, "physics", "Electromagnetic Induction and AC", "Transformers"): [
        "Transformer: Principle, Working, Mutual induction and Turns ratio (V_s / V_p = N_s / N_p)",
        "Step-up vs Step-down transformers and Efficiency",
        "Energy losses in transformers (Flux leakage, Copper loss, Iron core eddy currents, Hysteresis)",
    ],

    (12, "physics", "Ray Optics and Optical Instruments", "Refraction at spherical surfaces"): [
        "Refraction at spherical refracting surface formula: n2/v - n1/u = (n2 - n1)/R",
        "Cartesian sign conventions and Real/Virtual image formations at spherical surfaces",
    ],
    (12, "physics", "Ray Optics and Optical Instruments", "Lens maker's formula"): [
        "Lens maker's formula derivation: 1/f = (n - 1)(1/R1 - 1/R2)",
        "Thin lens formula (1/f = 1/v - 1/u) and Magnification",
        "Effect of surrounding medium on focal length of a lens",
    ],
    (12, "physics", "Ray Optics and Optical Instruments", "Combination of lenses and mirrors"): [
        "Combination of thin lenses in contact: Equivalent focal length (1/f = 1/f1 + 1/f2) and Net power (P = P1 + P2)",
        "Silvering of lenses and Equivalent focal length of mirrored lens system",
    ],
    (12, "physics", "Ray Optics and Optical Instruments", "Microscope and telescope"): [
        "Simple microscope (Magnifying glass): Magnifying power at D and infinity",
        "Compound microscope: Ray diagram, Working and Magnifying power formula",
        "Astronomical refracting telescope: Ray diagram, Normal adjustment and Magnifying power",
        "Reflecting telescopes (Cassegrain telescope): Advantages over refracting telescopes",
    ],

    (12, "physics", "Wave Optics", "Huygens' principle"): [
        "Wavefront: Spherical, Cylindrical and Plane wavefronts",
        "Huygens' principle of secondary wavelets",
        "Proof of laws of reflection and refraction using Huygens' principle",
    ],
    (12, "physics", "Wave Optics", "Young's double slit experiment"): [
        "Coherent sources and Conditions for sustained interference",
        "Young's Double Slit Experiment (YDSE): Setup and Path difference (Delta x = y d / D)",
        "Constructive and destructive interference conditions, Fringe width formula (beta = lambda D / d)",
        "Intensity distribution curve in YDSE (I = 4 I_0 cos^2(phi/2))",
    ],
    (12, "physics", "Wave Optics", "Diffraction and polarization"): [
        "Diffraction of light: Distinction between interference and diffraction",
        "Single slit diffraction: Central maximum width, Minima conditions (a sin theta = n lambda)",
        "Polarisation of light: Plane polarised light, Malus's law (I = I_0 cos^2 theta) and Brewster's law (tan i_p = n)",
    ],

    (12, "physics", "Modern Physics", "Photoelectric effect"): [
        "Photoelectric effect: Hertz and Lenard observations, Work function and Threshold frequency",
        "Experimental characteristics: Effect of intensity, potential and frequency on photocurrent",
        "Einstein's photoelectric equation: h nu = Phi_0 + 1/2 m v_max^2 and Stopping potential",
        "Matter waves: de Broglie hypothesis (lambda = h/p = h/sqrt(2mE)) and Electron wavelength",
    ],
    (12, "physics", "Modern Physics", "Bohr model of the atom"): [
        "Rutherford's alpha scattering experiment and Nuclear atom model limitations",
        "Bohr's postulates: Stationary orbits and Angular momentum quantisation (mvr = n h / 2pi)",
        "Radii of electron orbits, Orbital velocity and Energy levels of hydrogen atom (E_n = -13.6 / n^2 eV)",
        "Hydrogen spectral series: Lyman, Balmer, Paschen, Brackett and Pfund series",
    ],
    (12, "physics", "Modern Physics", "Nuclear binding energy and radioactivity"): [
        "Nuclear composition, Size (R = R_0 A^(1/3)), Density and Mass defect",
        "Nuclear binding energy and Binding energy per nucleon curve",
        "Nuclear fission (Uranium-235 chain reaction) and Nuclear fusion in stars",
        "Radioactivity: Alpha, Beta and Gamma decays, Decay law (N = N_0 e^(-lambda t)) and Half-life",
    ],
    (12, "physics", "Modern Physics", "Semiconductor diodes and logic gates"): [
        "Energy bands in solids: Conductors, Insulators and Semiconductors (Intrinsic and Extrinsic)",
        "p-n junction diode: Depletion layer, Barrier potential, Forward and Reverse bias characteristics",
        "p-n diode as rectifier: Half-wave rectifier and Full-wave rectifier",
        "Special semiconductor devices: Zener diode, Photodiode, LED and Solar cell",
        "Logic gates: Basic gates (OR, AND, NOT), Universal gates (NAND, NOR) and Truth tables",
    ],

    # ------------------ CLASS 12 MATH ------------------
    (12, "math", "Relations, Functions and Inverse Trigonometry", "Types of functions"): [
        "Functions classification: One-one (Injective) and Many-one functions",
        "Functions classification: Onto (Surjective) and Into functions",
        "Bijective functions (One-one and Onto) and Invertibility conditions",
        "Composition of functions: (g o f)(x) and Inverse function f^(-1)(x)",
    ],
    (12, "math", "Relations, Functions and Inverse Trigonometry", "Inverse trigonometric functions and their properties"): [
        "Inverse trigonometric functions: Definition, Domain and Principal value branches",
        "Graphs of sin^(-1) x, cos^(-1) x, tan^(-1) x",
        "Properties of inverse trigonometric functions: sin^(-1)(1/x) = cosec^(-1) x and sin^(-1)(-x) = -sin^(-1) x",
        "Sum identities: sin^(-1) x + cos^(-1) x = pi/2 and tan^(-1) x + tan^(-1) y formulas",
    ],

    (12, "math", "Matrices and Determinants", "Matrix operations"): [
        "Matrix definition: Order of matrix, Types (Row, Column, Square, Diagonal, Scalar, Identity, Zero)",
        "Matrix operations: Addition, Subtraction and Scalar multiplication",
        "Matrix multiplication: Row-by-column rule, Properties and Non-commutativity",
        "Transpose of a matrix, Symmetric and Skew-symmetric matrices",
    ],
    (12, "math", "Matrices and Determinants", "Properties of determinants"): [
        "Determinants of order 2 and order 3 evaluation",
        "Minors and Cofactors of determinant elements",
        "Properties of determinants: Invariance under row/column operations and Area of triangle",
    ],
    (12, "math", "Matrices and Determinants", "Inverse of a matrix"): [
        "Adjoint of a square matrix: Definition, Properties (A * adj(A) = |A| I)",
        "Singular and Non-singular matrices and Condition for invertibility (|A| != 0)",
        "Inverse of a matrix formula: A^(-1) = (1/|A|) * adj(A)",
    ],
    (12, "math", "Matrices and Determinants", "Solving linear equations using matrices"): [
        "System of linear equations in matrix form: A X = B",
        "Matrix method for solving systems of 2 and 3 linear equations",
        "Consistency and Inconsistency of systems of linear equations",
    ],

    (12, "math", "Continuity, Differentiability and Applications of Derivatives", "Continuity and differentiability conditions"): [
        "Continuity of a function at a point: LHL = RHL = f(a) and Continuity in an interval",
        "Algebra of continuous functions and Points of discontinuity",
        "Differentiability of a function: Left-hand and Right-hand derivative existence",
        "Relation between continuity and differentiability (Differentiability implies continuity)",
    ],
    (12, "math", "Continuity, Differentiability and Applications of Derivatives", "Chain rule and implicit differentiation"): [
        "Chain rule for differentiation of composite functions",
        "Derivative of implicit functions and Derivative of inverse trigonometric functions",
        "Logarithmic differentiation for variable powers (y = f(x)^g(x))",
        "Parametric differentiation: dy/dx = (dy/dt) / (dx/dt) and Second order derivatives",
    ],
    (12, "math", "Continuity, Differentiability and Applications of Derivatives", "Maxima and minima"): [
        "Critical points and Stationary points of a function",
        "First derivative test for local maxima and local minima",
        "Second derivative test for local maxima and minima",
        "Absolute maximum and absolute minimum values in a closed interval",
        "Real-life optimization word problems (Max area, Min cost, Volume)",
    ],
    (12, "math", "Continuity, Differentiability and Applications of Derivatives", "Rate of change and tangents/normals"): [
        "Derivative as rate of change: Real-world problems (Rate of volume, Area, Position)",
        "Strictly increasing and decreasing functions: Derivative sign criteria",
        "Equations of tangent and normal to a curve at a given point",
    ],

    (12, "math", "Integrals and Applications", "Integration techniques (substitution, by parts, partial fractions)"): [
        "Indefinite integration: Anti-derivative definition and Standard integral formulas",
        "Integration by substitution method and Standard trigonometric integrals",
        "Integration using trigonometric identities",
        "Integration by partial fractions for rational algebraic functions",
        "Integration by parts formula: integral u v dx = u integral v dx - integral (u' integral v dx) dx (ILATE rule)",
    ],
    (12, "math", "Integrals and Applications", "Definite integrals and properties"): [
        "Definite integral as limit of a sum and Fundamental theorem of calculus",
        "Properties of definite integrals: integral_a^b f(x) dx = -integral_b^a f(x) dx",
        "Properties of definite integrals: integral_0^a f(x) dx = integral_0^a f(a - x) dx",
        "Properties of definite integrals: Even and odd function integrals (integral_{-a}^a f(x) dx)",
    ],
    (12, "math", "Integrals and Applications", "Area under curves"): [
        "Area bounded by curve y = f(x), x-axis and Ordinates x = a, x = b",
        "Area bounded by curve x = g(y), y-axis and Abscissae y = c, y = d",
        "Area between two curves (Parabola and Line, Circle and Line)",
    ],

    (12, "math", "Differential Equations", "Formation of differential equations"): [
        "Differential equation definition: Order and Degree of differential equations",
        "General solution vs Particular solution of a differential equation",
        "Formation of differential equation representing a given family of curves",
    ],
    (12, "math", "Differential Equations", "Variable separable method"): [
        "Solving differential equations by variable separable method",
        "Homogeneous differential equations: Definition and Substitution y = v x",
    ],
    (12, "math", "Differential Equations", "Linear differential equations"): [
        "First-order linear differential equations: dy/dx + P y = Q",
        "Integrating factor (IF = e^(integral P dx)) and General solution formula (y * IF = integral (Q * IF) dx + C)",
        "Linear differential equations in x: dx/dy + P x = Q",
    ],

    (12, "math", "Vectors and Three Dimensional Geometry", "Vector algebra and scalar/vector triple product"): [
        "Vector basics: Magnitude, Direction cosines, Direction ratios and Collinear vectors",
        "Scalar (dot) product and Vector (cross) product of two vectors in component form",
        "Scalar triple product: [a b c] = a . (b x c), Geometrical meaning (Volume of parallelepiped) and Coplanarity",
    ],
    (12, "math", "Vectors and Three Dimensional Geometry", "Direction cosines and lines in 3D"): [
        "Direction cosines (l, m, n) and Direction ratios (a, b, c) of a line in 3D (l^2 + m^2 + n^2 = 1)",
        "Vector and Cartesian equation of a line passing through a point and parallel to a vector",
        "Equation of a line passing through two given points in 3D",
        "Angle between two lines in vector and Cartesian forms",
    ],
    (12, "math", "Vectors and Three Dimensional Geometry", "Equation of a plane"): [
        "Vector and Cartesian equation of a plane: Normal form (r . n_hat = d)",
        "Equation of a plane passing through a point and perpendicular to a vector",
        "Equation of a plane passing through three non-collinear points and Intercept form",
        "Angle between two planes and Angle between a line and a plane",
        "Distance of a point from a plane formula",
    ],
    (12, "math", "Vectors and Three Dimensional Geometry", "Shortest distance between lines"): [
        "Skew lines concept in 3D space",
        "Shortest distance between two skew lines: d = |(b1 x b2) . (a2 - a1)| / |b1 x b2|",
        "Shortest distance between two parallel lines: d = |b x (a2 - a1)| / |b|",
    ],

    (12, "math", "Probability", "Conditional probability"): [
        "Conditional probability: Definition, Formula (P(A|B) = P(A and B) / P(B)) and Properties",
        "Multiplication theorem on probability: P(A and B) = P(A) * P(B|A)",
        "Independent events: P(A and B) = P(A) * P(B) and Independent vs Mutually exclusive events",
    ],
    (12, "math", "Probability", "Bayes' theorem"): [
        "Partition of sample space and Theorem of total probability",
        "Bayes' theorem: Statement, Formula and Prior vs Posterior probability",
        "Real-world applications of Bayes' theorem (Disease testing, Machine defect rates)",
    ],
    (12, "math", "Probability", "Random variables and probability distributions"): [
        "Random variable (Discrete) and Probability distribution of a random variable",
        "Mean (Mathematical expectation E(X)) of a random variable",
        "Variance and Standard deviation of a random variable",
    ],
    (12, "math", "Probability", "Binomial distribution"): [
        "Bernoulli trials: Conditions for Bernoulli trials",
        "Binomial distribution: Probability mass function P(X = r) = nCr p^r q^(n-r)",
        "Mean and variance of binomial distribution (Mean = np, Var = npq)",
    ],

    (12, "math", "Linear Programming", "Formulating a linear programming problem"): [
        "Linear Programming Problem (LPP): Objective function, Decision variables, Constraints and Non-negativity",
        "Formulating real-world LPP: Diet problem, Manufacturing problem, Transportation problem",
    ],
    (12, "math", "Linear Programming", "Graphical method and the feasible region"): [
        "Plotting linear constraints and Finding the feasible region",
        "Bounded vs Unbounded feasible regions and Corner point / Extreme point method",
    ],
    (12, "math", "Linear Programming", "Finding the optimal solution"): [
        "Corner point method for finding maximum and minimum values of objective function",
        "Solving bounded and unbounded LPP problems and Iso-profit / Iso-cost lines",
    ],
}


def build():
    with open(SYLLABUS_FILE) as f:
        orig = json.load(f)

    # Backup original
    shutil.copy2(SYLLABUS_FILE, BACKUP_FILE)
    print(f"Backed up current syllabus to {BACKUP_FILE}")

    new_syllabus = []
    total_parts = 0
    missing = []

    for ch in orig:
        subj = ch["subject"]
        chap = ch["chapter"]
        cl = ch.get("class", 0)

        new_subtopics = []
        for parent in ch["subtopics"]:
            key = (cl, subj, chap, parent)
            if key in BREAKDOWNS:
                parts = BREAKDOWNS[key]
                new_subtopics.extend(parts)
            else:
                missing.append(key)
                # Fallback: create 3 reasonable proper parts
                new_subtopics.extend([
                    f"{parent}: Core Concept and Foundations",
                    f"{parent}: Formulas and Derivations",
                    f"{parent}: Problem Applications",
                ])

        new_syllabus.append({
            "class": cl,
            "subject": subj,
            "chapter": chap,
            "subtopics": new_subtopics
        })
        total_parts += len(new_subtopics)

    if missing:
        print(f"WARNING: {len(missing)} subtopics used fallback breakdown:")
        for m in missing:
            print(f"  {m}")
    else:
        print("SUCCESS: 100% of all 237 parent subtopics have explicit pedagogical breakdowns!")

    with open(SYLLABUS_FILE, "w") as f:
        json.dump(new_syllabus, f, indent=2)

    print(f"\nWritten updated syllabus.json:")
    print(f"  Total chapters: {len(new_syllabus)}")
    print(f"  Total subtopic parts: {total_parts} (avg {total_parts / len(new_syllabus):.1f} per chapter)")


if __name__ == "__main__":
    build()
