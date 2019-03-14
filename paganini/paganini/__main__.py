from __future__ import unicode_literals, print_function
import paganini.tuner as pt

def main(args=None):

    __author__    = "Maciej Bendkowski and Sergey Dovgal"
    __copyright__ = "Copyright (C) 2017-2019 Maciej Bendkowski and Sergey Dovgal"
    __license__   = "Public Domain"
    __version__   = "0.2955977425220"

    flag_debug = False

    #
    ##
    ### IMPORTS
    ##
    #

    try:
        import sys
        import os
        import os.path
        import argparse
        from argparse import RawTextHelpFormatter

    except:
        print("Something went wrong, cannot import packages 'sys', 'os' or 'argparse'.")
        exit(1)

    if sys.version_info.major != 3:
        sys.stderr.write('You are using Python 2, consider using Python 3.\n')

    #
    ##
    ###  PARSING COMMAND LINE ARGUMENTS
    ##
    #

    class bcolors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    example_string = bcolors.BOLD + """Example """ + bcolors.ENDC + """

    Consider a system for marking abstractions in lambda-terms:

    L = z L^2 + u z L + D
    D = z + z D

    We want to have 40% of abstractions, so we encode all the variables and
    functions into a single vector [z, u, L, D] and start with
    the virtual specification

    2 1
    0.4
    3
    1 1 1 0
    1 0 2 0
    0 0 0 1
    2
    1 0 0 0
    1 0 0 1

    Next, we compress each of the above equations using
    the following sparse vector notation:

    2 1
    0.4
    3
    (1,0) (1,1) (1,2)
    (1,0) (2,2)
    (1,3)
    2
    (1,0)
    (1,0) (1,3)

    In other words, for each equation we write down only its non-zero monomials
    with respective occurrences. Such an input format encodes the system
    corresponding to lambda-terms.
    """

    parser = argparse.ArgumentParser(
            description= bcolors.BOLD + """Welcome to paganini.py! """ +
            bcolors.ENDC,
            epilog = example_string,
            formatter_class=RawTextHelpFormatter)

    parser.add_argument('-i', '--input', dest='input', nargs=1,
            required=False, help="Name of the input file")
    parser.add_argument('--from-stdin', dest='from_stdin', action='store_true',
            required=False, help="Take the input from stdin")
    parser.add_argument('-s', '--solver', dest='solver', nargs=1,
            required=False, help="Solver: [CVXOPT, SCS, ECOS]. Default is ECOS.")
    parser.add_argument('-p', '--precision', dest='precision', nargs=1,
            type=float,
            required=False, help="Precision. Defaults to 1e-20.")
    parser.add_argument('-m', '--max-iters', dest='maxiters', nargs=1, type=int,
            required=False, help="Maximum number of iterations.")
    parser.add_argument('-t', '--type', dest='type',
            required=False, help="Type of the grammar: [rational, algebraic]")

    arguments = parser.parse_args()

    if arguments.from_stdin==False and arguments.input==None:
        parser.print_help(sys.stderr)
        exit(1)

    if arguments.from_stdin!=False and arguments.input!=None:
        sys.stderr.write('Choose either stdin or filename for input\n')
        parser.print_help(sys.stderr)
        exit(1)

    sys.stderr.write("Importing packages...\n")

    #
    ##
    ### IMPORT HEAVY PACKAGES
    ##
    #

    #-- Better hints at non-installed packages
    list_of_noninstalled_packages = []

    # --- cvxopt is truly necessary
    try:
        import cvxpy
    except:
        list_of_noninstalled_packages += ['cvxpy']

    # --- sympy is an insurance from exponent overflow
    # -- It will be removed for practical purposes and replaced by bounded region
    # feasible subset.
    try:
        import sympy
    except:
        list_of_noninstalled_packages += ['sympy']

    # --- scipy is required for sparse matrices.
    try:
        from scipy import sparse
    except:
        list_of_noninstalled_packages += ['scipy']

    try:
        import numpy as np
    except:
        list_of_noninstalled_packages += ['numpy']

    try:
        from six.moves import range
    except:
        list_of_noninstalled_packages += ['six']

    if len(list_of_noninstalled_packages) > 0:
        sys.stderr.write("""It seems that you need to install some packages.
    Please be patient and type into your command line
        pip2 install """ + ' '.join(list_of_noninstalled_packages) + """
    If you have only Python2 installed, you can also try
        pip install """ + ' '.join(list_of_noninstalled_packages) + """
    Good luck!
    """)
        sys.exit(1)

    ### PRECISION

    np.set_printoptions(precision=14)


    sys.stderr.write("Started concerto...\n")

    filename = arguments.input[0] if arguments.input else None
    precision = 1e-20
    if arguments.precision != None:
        try:
            precision = float(arguments.precision[0])
        except:
            raise Exception("Precision should be a float!")
    is_rational = False
    if arguments.type == 'rational':
        sys.stderr.write("System is of rational type\n")
        is_rational = True
    elif arguments.type == 'algebraic':
        is_rational = False
    elif arguments.type != None:
        sys.stderr.write("Type of the grammar not recognized, using algebraic.\n")

    if filename and not os.path.isfile(filename):
        raise Exception("File doesn't exist!", filename)

    #
    ##
    ### MAIN CODE
    ##
    #

    # set default error file name
    err_filename = filename if filename else "stdin"

    input_error_string = """
    Input format error in '""" + err_filename + """'!
    Type paganini -h for help and examples.
    """

    FILE = open(filename,'r') if filename else sys.stdin

    # Read the number of variables and functions

    vec = FILE.readline().split()
    assert np.size(vec) >= 2, input_error_string
    try:
        number_of_functions = int(vec[0])
        number_of_variables = int(vec[1])
        total_number_of_variables = number_of_functions + number_of_variables + 1
    except:
        raise Exception(input_error_string)
    assert number_of_functions > 0, '\nThe number of functions should be a positive integer.\n'
    assert number_of_variables >= 0, '\nThe number of functions should be nonnegative integer.\n'

    # Read the frequences
    vec = FILE.readline().split()
    assert np.size(vec) >= number_of_variables,\
                '\nThe number of frequences should be equal to number of variables.\n'
    if number_of_variables > 0:
        try:
            freq = [float(elem) for elem in vec]
        except:
            raise Exception(input_error_string)
    else:
        freq = []

    sys.stderr.write("Reading the coefficients...\n")

    if is_rational:
        sys_type = pt.Type.RATIONAL
        sys_type.eps = precision
    else:
        sys_type = pt.Type.ALGEBRAIC
        sys_type.feastol = precision

    if arguments.solver != None:
        if (arguments.solver[0] == 'CVXOPT'):
            sys_type.solver = cvxpy.CVXOPT
        elif (arguments.solver[0] == 'SCS'):
            sys_type.solver = cvxpy.SCS
        elif (arguments.solver[0] == 'ECOS'):
            sys_type.solver = cvxpy.ECOS
        else:
            sys.stderr.write("Solver not recognized. Using ECOS by default.\n")

    if arguments.maxiters != None:
        sys_type.max_iters = int(arguments.maxiters[0])


    params = pt.Params(sys_type)
    spec = pt.Specification()

    variables = []
    variables.append(spec.variable()) # z

    for idx in range(number_of_variables):
        variables.append(spec.variable(freq[idx]))

    for idx in range(number_of_functions):
        variables.append(spec.variable())

    for n_equation in range(number_of_functions):
        vec = FILE.readline().split()
        assert np.size(vec) >= 1,\
                'What is the number of monomials in equation '+ n_equation + '?\n'

        equation = []
        n_monomials = int(vec[0])
        for monomial in range(n_monomials):
            vec = FILE.readline().split()

            definition = []
            for elem in vec:
                arr = elem[1:-1].split(',')
                a, b = int(arr[0]), int(arr[1])
                definition.append(variables[b] ** a)

            if len(vec) > 0:
                expr = definition[0]
                for idx in range(len(vec) - 1):
                    expr = expr * definition[idx + 1]

                equation.append(expr)
            else:
                equation.append(1) # monomial equivalent to the constant one

        spec.add(variables[1 + number_of_variables + n_equation], equation)

    sys.stderr.write("Solving the optimization problem... ")

    old_stdout = sys.stdout
    sys.stdout = sys.stderr

    try:
        status = spec.run_singular_tuner(variables[0], params)

    except:
        sys.stderr.write("Solver " + str(solver) + " failed :(")
        exit(1)

    sys.stderr.write("Solved.\n")
    sys.stdout = old_stdout

    print ('\n'.join([
            str(v.value)
            for v in variables
          ]))

if __name__ == "__main__":
    main()
