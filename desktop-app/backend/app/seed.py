import json
from .models import Subject, Lesson, Question

SUBJECTS = [
    ("Python Programming", "Write clear, useful Python from first steps to practical automation.", "🐍", ["Getting started and values", "Decisions and loops", "Functions and decomposition", "Lists, tuples and dictionaries", "Strings and file handling", "Errors and modules", "Object oriented Python", "Testing and APIs", "Projects and clean code"]),
    ("C Programming", "Understand memory-aware programming, from expressions to data structures.", "⚙️", ["C tools and program structure", "Types and operators", "Branches and loops", "Functions and scope", "Arrays and strings", "Pointers and memory", "Structs and files", "Dynamic memory and lists", "Testing and systems project"]),
    ("Java Programming", "Build robust Java programs with classes, collections and modern practices.", "☕", ["Java setup and syntax", "Types and expressions", "Control flow", "Methods and arrays", "Classes and encapsulation", "Inheritance and interfaces", "Collections and generics", "Exceptions and files", "Testing and application project"]),
    ("Mathematics", "Build mathematical fluency in algebra, functions, calculus and statistics.", "📐", ["Number sense and algebra", "Equations and inequalities", "Functions and graphs", "Geometry and trigonometry", "Sequences and series", "Limits and continuity", "Differentiation and applications", "Integration and area", "Probability and statistics"]),
    ("Physics", "Connect physical models to measurements, mechanics, waves and electricity.", "⚡", ["Measurement and units", "Vectors and motion", "Forces and Newton laws", "Work, energy and momentum", "Rotation and gravitation", "Oscillations and waves", "Heat and thermodynamics", "Electricity and circuits", "Magnetism and modern physics"]),
    ("Chemistry", "Learn how atomic structure explains bonding, reactions and materials.", "🧪", ["Matter and measurement", "Atoms and periodic trends", "Chemical bonding", "Moles and equations", "Reaction types and stoichiometry", "States of matter and gases", "Acids, bases and equilibrium", "Redox and electrochemistry", "Organic chemistry and applications"]),
    ("Computer Science", "Explore how data, algorithms, systems and networks power software.", "💻", ["Digital systems and abstraction", "Binary and data representation", "Algorithms and pseudocode", "Data structures", "Operating systems", "Databases and SQL", "Networks and web", "Security and software engineering", "Computing project and ethics"]),
    ("Artificial Intelligence", "Study data-driven learning, neural models and responsible AI.", "🤖", ["AI concepts and problem solving", "Python tools for data", "Data preparation and visualization", "Search and optimization", "Supervised learning", "Model evaluation and bias", "Neural network foundations", "Language models and applications", "Responsible AI capstone"]),
    ("Data Structures and Algorithms", "Choose efficient structures and reason about algorithm performance.", "🧩", ["Complexity and problem solving", "Arrays and strings", "Linked lists and stacks", "Queues and hashing", "Trees and traversals", "Heaps and priority queues", "Sorting and searching", "Graphs and shortest paths", "Dynamic programming and capstone"]),
    ("English Communication", "Communicate ideas clearly in academic, professional and digital settings.", "🗣️", ["Reading for meaning", "Grammar and sentence clarity", "Vocabulary and word choice", "Paragraph structure", "Academic reading and notes", "Essay development", "Speaking and presentation", "Professional email and collaboration", "Research communication portfolio"]),
]

def lesson_text(subject, title, month, week):
    # The monthly sequence is deliberately cumulative: concepts, guided examples, practice, then review.
    phase = ["Build the core idea", "Work through a guided example", "Apply the idea to a new problem", "Review, connect and self-check"][week - 1]
    if subject == "Mathematics":
        details = "Define each variable, state the rule you choose, substitute values carefully, and check the result in the original problem. Show each algebraic step so an error can be found."
        example = "Solve 2x + 3 = 11: subtract 3 to get 2x = 8, then divide by 2. Therefore x = 4; substituting gives 2(4)+3 = 11."
        exercise = "Solve 3x - 5 = 16. Write each inverse operation and verify your solution by substitution."
    elif subject in ("Python Programming", "C Programming", "Java Programming"):
        lang = {"Python Programming":"Python", "C Programming":"C", "Java Programming":"Java"}[subject]
        code = {"Python":"total = sum([3, 5, 8])\nprint(total)  # 16", "C":"int values[] = {3, 5, 8};\nint total = 0;\nfor (int i = 0; i < 3; i++) total += values[i];", "Java":"int[] values = {3, 5, 8};\nint total = 0;\nfor (int value : values) total += value;\nSystem.out.println(total);"}[lang]
        details = "Trace the program with a small input before generalizing. Identify the data type, the state that changes, and the expected output. Prefer a small function with one clear responsibility."
        example = code
        exercise = "Adapt the example to calculate the average of four values. Handle the denominator explicitly and test with values 2, 4, 6, 8."
    elif subject == "Physics":
        details = "Start with a system boundary and a diagram. List knowns with units, select a physical law, solve symbolically, and check dimensions before calculating."
        example = "For constant acceleration, v = u + at. Starting at 2 m/s and accelerating at 3 m/s² for 4 s gives v = 2 + 3×4 = 14 m/s."
        exercise = "A cyclist starts at 5 m/s and accelerates at 1.5 m/s² for 6 s. Find final speed and show units."
    elif subject == "Chemistry":
        details = "Keep track of particles and conservation. Write a balanced equation first, convert quantities to moles when comparing amounts, and label units at every stage."
        example = "2H₂ + O₂ → 2H₂O shows a 2:1:2 mole ratio. Four moles of H₂ need two moles of O₂ and can form four moles of H₂O if oxygen is sufficient."
        exercise = "Balance N₂ + H₂ → NH₃, then state the mole ratio of nitrogen to ammonia."
    elif subject == "English Communication":
        details = "Read for audience, purpose and evidence. Build one main claim, support it with a specific example, and revise sentences for direct wording and logical flow."
        example = "Vague: 'There are many benefits to feedback.' Clear: 'Weekly feedback helps students correct misconceptions before the next assessment.'"
        exercise = "Write a 4-sentence paragraph explaining why spaced practice helps learning. Include a claim, an example and a concluding link."
    else:
        details = "Define the problem, identify the input and output, then choose a representation that makes the important operation clear. Work a tiny example by hand before scaling up."
        example = "For a sorted list [2, 5, 8, 12, 17], binary search checks the middle value 8 first. Looking for 12 discards the lower half, then finds 12 in the remaining range."
        exercise = "Describe an algorithm to find the largest item in a list. State its time complexity and trace it on [4, 1, 7, 3]."
    return ("%s. %s. Month %d focuses on %s. %s" % (phase, title, month, title.lower(), details), example, exercise)

def subject_questions(subject):
    banks = {
        "Python Programming": [
            ("What does len([4, 7, 9]) return?", ["2", "3", "4", "79"], 1, "The list contains three elements."),
            ("Which keyword starts a named function in Python?", ["func", "define", "def", "function"], 2, "Python uses def followed by the function name."),
            ("What is the value of 2 ** 3?", ["5", "6", "8", "9"], 2, "The ** operator raises a value to a power: 2 × 2 × 2 = 8."),
        ],
        "C Programming": [
            ("What is the index of the first element in a C array?", ["0", "1", "-1", "It depends"], 0, "C arrays use zero-based indexing."),
            ("Which operator gives the address of a variable?", ["*", "&", "%", "->"], 1, "The unary & operator produces a variable's address."),
            ("Which header declares printf?", ["<stdlib.h>", "<string.h>", "<stdio.h>", "<math.h>"], 2, "printf is declared in the standard input/output header."),
        ],
        "Java Programming": [
            ("Which keyword creates a new Java object?", ["class", "new", "this", "make"], 1, "new constructs an instance of a class."),
            ("How do you compare String contents in Java?", ["Use ==", "Use equals()", "Use =", "Use compare"], 1, "equals() compares String contents; == compares references."),
            ("How do you access the number of items in an array?", ["array.size()", "array.count", "array.length", "length(array)"], 2, "Java arrays expose their size through the length field."),
        ],
        "Mathematics": [
            ("Solve 2x + 3 = 11.", ["x = 3", "x = 4", "x = 5", "x = 7"], 1, "Subtract 3 to get 2x = 8, then divide by 2."),
            ("What is the slope between (1, 2) and (3, 6)?", ["1", "2", "3", "4"], 1, "Slope = (6 − 2) / (3 − 1) = 2."),
            ("What is the derivative of x²?", ["x", "2x", "2", "x³"], 1, "The power rule gives d(x²)/dx = 2x."),
        ],
        "Physics": [
            ("Which is the SI unit of acceleration?", ["m/s", "m/s²", "kg·m/s", "N"], 1, "Acceleration is change in velocity per time, measured in m/s²."),
            ("A 2 kg object accelerates at 3 m/s². What net force acts on it?", ["1.5 N", "5 N", "6 N", "9 N"], 2, "Newton's second law gives F = ma = 2 × 3 = 6 N."),
            ("In a series circuit, which quantity is the same through each component?", ["Current", "Voltage", "Resistance", "Power"], 0, "The same current flows through every component in a series path."),
        ],
        "Chemistry": [
            ("The atomic number of an element counts its number of…", ["neutrons", "protons", "shells", "isotopes"], 1, "Atomic number is the number of protons in the nucleus."),
            ("What coefficient balances H₂ + O₂ → H₂O?", ["1, 1, 1", "2, 1, 2", "1, 2, 1", "2, 2, 1"], 1, "2H₂ + O₂ → 2H₂O conserves both hydrogen and oxygen atoms."),
            ("A solution with pH 3 is…", ["acidic", "neutral", "basic", "pure water"], 0, "Values below 7 are acidic at standard conditions."),
        ],
        "Computer Science": [
            ("How many bits are in one byte?", ["4", "8", "16", "32"], 1, "A byte is conventionally eight bits."),
            ("What is a primary key used for in a database table?", ["To uniquely identify each row", "To encrypt every column", "To sort all rows", "To store images"], 0, "A primary key uniquely identifies a record."),
            ("Which operating system component schedules processes?", ["Compiler", "CPU scheduler", "Router", "Text editor"], 1, "The CPU scheduler selects which ready process runs next."),
        ],
        "Artificial Intelligence": [
            ("Supervised learning uses training examples that include…", ["Labels or target answers", "Only random noise", "No data", "Hardware instructions"], 0, "Supervised examples pair inputs with known target labels."),
            ("A model performs well on training data but poorly on new data. This is…", ["Underflow", "Overfitting", "Normalization", "Clustering"], 1, "Overfitting means the model has not generalized to unseen examples."),
            ("Why keep a test set separate from training?", ["To estimate performance on unseen data", "To make training faster", "To add labels", "To duplicate the input"], 0, "A held-out test set provides an independent performance check."),
        ],
        "Data Structures and Algorithms": [
            ("Which structure follows last-in, first-out order?", ["Queue", "Stack", "Tree", "Graph"], 1, "A stack removes the most recently added item first."),
            ("Binary search requires the data to be…", ["Sorted", "Random", "Unique strings", "Stored on disk"], 0, "Each comparison discards half of a sorted search range."),
            ("How does linear search scale with n items in the worst case?", ["O(1)", "O(log n)", "O(n)", "O(n²)"], 2, "It may inspect each item once, so work grows linearly."),
        ],
        "English Communication": [
            ("What is the main job of a topic sentence?", ["Introduce the paragraph's central idea", "Add an unrelated detail", "Repeat the title", "End the essay"], 0, "A topic sentence gives the paragraph a clear focus."),
            ("Which sentence uses active voice?", ["The report was written by Maya.", "Maya wrote the report.", "The report is being written.", "The report had been written."], 1, "The subject Maya performs the action wrote."),
            ("Before writing a presentation, what should you identify first?", ["Audience and purpose", "Font size", "Slide count", "The conclusion only"], 0, "Audience and purpose guide content, tone and structure."),
        ],
    }
    return banks.get(subject, [
        ("What should a strong worked example include?", ["Clear steps and a check", "Only the final answer", "Unexplained symbols", "A guess"], 0, "Steps and a check make reasoning visible."),
        ("What is a useful first move on a new problem?", ["Identify knowns and the goal", "Skip the prompt", "Change the data", "Memorize a random rule"], 0, "Listing knowns and the goal helps select an appropriate method."),
        ("How can you check whether a result makes sense?", ["Compare it with the problem and assumptions", "Ignore the units", "Repeat the same guess", "Avoid estimating"], 0, "A reasonableness check can reveal mistakes."),
    ])

def quiz_questions(subject):
    bank=list(subject_questions(subject))
    topics=next((row[3] for row in SUBJECTS if row[0] == subject),["Foundations","Key vocabulary","Core methods","Worked examples","Practice","Review","Applications","Projects","Reflection"])
    for month, topic in enumerate(topics[:7], 1):
        distractors=[topics[(month+1)%9],topics[(month+3)%9],topics[(month+5)%9]]
        options=[topic]+distractors
        # Rotate options so correct answers are not always in position A.
        shift=month%4
        options=options[shift:]+options[:shift]
        answer=options.index(topic)
        bank.append(("In the nine-month %s curriculum, which topic is studied in Month %d?" % (subject,month),options,answer,"Month %d focuses on %s." % (month,topic)))
    return bank

def store_questions(db, subject_id, name):
    for prompt, options, answer, explanation in quiz_questions(name):
        db.add(Question(subject_id=subject_id,month=1,prompt=prompt,options=json.dumps(options),answer=answer,explanation=explanation))

def seed(db):
    if db.query(Subject).count():
        for subject in db.query(Subject).all():
            if db.query(Question).filter_by(subject_id=subject.id).count() < 10:
                db.query(Question).filter_by(subject_id=subject.id).delete(synchronize_session=False)
                store_questions(db,subject.id,subject.name)
        db.commit()
        return
    for name, description, icon, topics in SUBJECTS:
        subject = Subject(name=name, description=description, icon=icon)
        db.add(subject); db.flush()
        for month, topic in enumerate(topics, 1):
            for week in range(1, 5):
                title = [topic + ": foundations", topic + ": worked example", topic + ": application", topic + ": review and mastery"][week-1]
                content, example, exercise = lesson_text(name, topic, month, week)
                level = "beginner" if month <= 3 else ("intermediate" if month <= 6 else "advanced")
                db.add(Lesson(subject_id=subject.id, month=month, week=week, title=title, content=content, example=example, exercise=exercise, level=level))
        store_questions(db,subject.id,name)
    db.commit()
