import glob


def statp(file_pattern:str) -> str:
    '''takes a file patern and returns the number of stationary points in each file that fits that pattern.

    Parameters
    ----------
    file_patern (str) :  a string that matches a certain string

    Returns
    -------
    a string that gives nomber of occurences and line numbers of stationary points

'''
    # String that will be returned later
    results_string = ""
    #Loop through each file name that matches the pattern
    for name in glob.glob(file_pattern):
        indexes = []
        count = 0
        with open(name,'r') as file:
            file_lines = file.readlines()
        #Loop through the lines of the file
        for index, line in enumerate(file_lines):
            #Add line numbers if stationary point is present
            if "-- Stationary point found." == line.strip("\n\t "):
                count = count + 1
                indexes.append(index)
        # Add results to results string
        results_string = results_string + f"{name+":":<35}{count}\n{indexes}\n"
    return results_string


class out_file_scraper:
    '''
    This is a parent file scraper class meant to be altered or used for scraping log files for computations. 
    
    Attributes
    ----------
    path : str
        a path to an output file
    
    file_list : list
        a list of strings where each item is the corrsponding line in the file.
'''

    def __init__(self, filepath : str) -> None:
        '''
        Initializes an out_file_scraper object using a filepath.

        Parameters
        ----------
            filepath : str
                The path to a general output file.
        Returns
        -------
            None
                Creates an out_file_scraper object
        '''
        self.path = filepath
        self.flag_functions = {}
        self.read_in_file()
        pass

    def read_in_file(self) -> None:
        '''
        Reads in a file and retruns a list where each line is an item in the list

        Parameters
        ----------
            file_name : str
                a path to an output file
        Returns
        -------
            None
                assignes self.file_list a list of all the lines in a file where each item in the list is an item.
        '''

        with open(self.path,"r") as file:
            self.file_list = file.readlines()
        pass


    def set_flag_function(self,flag:str,function_string:str) -> None:
        '''
        Create the flag_functions dictionary mapping flag strings to the subparsing functions

        Parameters
        ----------
            self
            flag : str
                this is the flag you plan to add to the flag_functions dictionary
            function_string : str
                this is the method you plan to call if the flag is found
        
        Returns
        -------
            None
                Adds to the self.flag_functions dictionary
        '''

        if flag not in self.flag_functions.keys():
            self.flag_functions[flag] = function_string
        else:
            raise Exception("The key", flag, "was already found in self.flag_functions" )
        pass
    
    
    def parse_outfile(self) -> None:
        '''
        Parses the outfile to generate all of the data you want to pull.

        Parameters
        ----------
            self

        Returns
        -------
            None
                Assigns all the values you are trying to pull by systematically calling yor parsing methods
        '''
        self.current_index = 0
        for index, line in enumerate(self.file_list):

            if index <= self.current_index:
                continue
            if (flag := line.strip(" \t\n")) in self.flag_functions.keys():
                eval(self.flag_functions[flag].format(index)) 


class g16_scraper(out_file_scraper):
    '''
    This is meant to be a general log file scraper for gaussian 16 log files

    Attributes
    ----------

    input_line : str
        this is the input line used in the original gjf file

    checkpoint_line : str
        The "%chk=" in the original gjf file

    nproc_line : str
        The "%nproc=" in the original gjf file

    memory_line : str
        The "%mem=" line in the original gjf file

    charge : int
        Represents the charge of the system in the original gjf file

    mult : int
        represents the multiplicity of the system in the original gjf file

    start_geometry: list[str]
        the starting geometry of the sytem in the original gjf file

    '''

    def __init__(self,filepath : str) -> None:
        '''
        Initializes the gaussian16 scraper object

        Parameters
        ----------
            filepath : str
                a string of the path to the file you would like to parse
        Returns
        -------
            None
                used simply to set up parsing flags and set flag functions
        '''

        super().__init__(filepath)
        self.input_line = ""
        input_flag = "Cite this work as:"
        self.set_flag_function(input_flag,"self.get_input_line({})")

        

    def get_input_line(self,index : int) -> None:
        '''
        Extracts the input information of the gaussian file 

        Parameters
        ----------
            self
            index : int
                The index of the line this parsing function's flag is found in the file_list
        Returns
        -------
            None
                assigns respective values to:
                    checkpoint_line : str
                    nproc_line :      str
                    memory_line :     str
                    input_line :      str
                    charge :          int
                    multiplicity :    int
                    start_geometry :  list[str]

        '''
        if self.input_line != "": 
            pass
        j = index
        line = self.file_list[j].strip(" \t\n")
        self.start_geometry = []
        self.charge = None
        self.multiplicity = None
        while self.start_geometry == []:
            if "%chk=" in line:
                
                self.checkpoint_line = line
            if "%nproc" in line:
                self.nproc_line = line
            if "%mem" in line:
                self.memory_line = line
            if self.input_line == "" and "---" in line:
                line = self.file_list[(j := j + 1)].strip(" \t\n")
                while "---" not in line:
                    self.input_line = self.input_line + line
                    line = self.file_list[(j := j + 1)].strip("\t\n")
                self.input_line = self.input_line.lower()
                self.input_line = self.input_line.strip(" \t\n")
            if self.start_geometry == [] and self.charge != None:
                while line != "":
                    self.start_geometry.append(line)
                    line = self.file_list[(j := j + 1)].strip(" \t\n")
            if "Charge = " in line:
                self.charge = int(line.split()[2])
                self.multiplicity = int(line.split()[5])

            line = self.file_list[(j := j + 1)].strip(" \t\n")


        self.current_index = j
        pass

    def recreate_gjf(self) -> str:
        '''
        Recreates the most basic starting gjf file (does not inclued anything after the starting geometry)

        Parameters
        ----------
            self

        Returns
        -------
            str
                a formatted string of a gjf file from the start of the run



        '''
        geometry = ""
        for i in self.start_geometry:
            geometry = geometry  + i + "\n"
        gjf_string =f"""{self.checkpoint_line}
{self.nproc_line}
{self.memory_line}
{self.input_line}

Title Card

{geometry}


"""
        return gjf_string
    


class g16_optfreq(g16_scraper):
    '''
    This is a gaussian16 log file scraper specifically for gausian jobs with the opt and freq specifications

    Attributes
    ----------
    zero_point_correction                          : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    thermal_correction_to_energy                   : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    thermal_correction_to_enthalpy                 : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    thermal_correction_to_gibbs_free_energy        : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    sum_of_electronic_and_zero_point_energies      : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    sum_of_electronic_and_thermal_enthalpies       : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.
    
    sum_of_electronic_and_thermal_energies         : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.

    sum_of_electronic_and_thermal_free_energies    : float
        unit: hartrees/particle
        gives the gaussian calculated floating point number.

    zero_point_energy                              :float
        unit: hartrees/particle
        gives the zero point energy of the system
    
    vibrational_thermal_contributions              : dict {str : tuple(str,float)}
        keys:
            "Thermal_Energy"
                unit : kcal/mol
                returns a list of tuples with the the name : str of the of the contribution at index 0 and the value : float at index 0
            "CV" (specific Heat)
                unit : cal/(mol * kelvin)
                returns a list of tuples with the the name : str of the of the contribution at index 0 and the value : float at index 0
            "S" (Entropy)
                unit : cal/(mol * kelvin)
                returns a list of tuples with the the name : str of the of the contribution at index 0 and the value : float at index 0

    '''

    def __init__(self,filepath:str) -> None:
        super().__init__(filepath)


        thermoschemistry_flag = "- Thermochemistry -"
        self.set_flag_function(thermoschemistry_flag,"self.get_thermochemistry_properties({})")


        
    def get_thermochemistry_properties(self, index : int) -> None:
        '''
        Assigns the thermochemistry properties
        
        Parameters
        ----------
            index : int
                The index of the starting line for the thermochemistry section in an opt freq gaussian job

        Returns
        -------
            None
                Assigns values to the following attributes:
                zero_point_correction                          : float
                thermal_correction_to_energy                   : float
                thermal_correction_to_enthalpy                 : float
                thermal_correction_to_gibbs_free_energy        : float
                sum_of_electronic_and_zero_point_energies      : float
                sum_of_electronic_and_thermal_energies         : float
                sum_of_electronic_and_thermal_enthalpies       : float
                sum_of_electronic_and_thermal_free_energies    : float
                zero_point_energy                              : float
                vibrational_thermal_contributions              : dict {str : tuple(str,float)}
        '''
        end_string = "-----------------------------------------"
        j = index + 2
        line = self.file_list[j].strip(" \t\n")

        while end_string not in line:

            if "Zero-point correction=" in line:
                self.zero_point_correction = float(line.split()[2])
            
            if "Thermal correction to Energy=" in line:
                self.thermal_correction_to_energy = float(line.split()[4])

            if "Thermal correction to Enthalpy=" in line:
                self.thermal_correction_to_enthalpy = float(line.split()[4])

            if "Thermal correction to Gibbs Free Energy=" in line:
                self.thermal_correction_to_gibbs_free_energy = float(line.split()[6])

            if "Sum of electronic and zero-point Energies=" in line:
                self.sum_of_electronic_and_zero_point_energies = float(line.split()[6])

            if "Sum of electronic and thermal Energies=" in line:
                self.sum_of_electronic_and_thermal_energies = float(line.split()[6])

            if "Sum of electronic and thermal Enthalpies=" in line:
                self.sum_of_electronic_and_thermal_enthalpies = float(line.split()[6])

            if "Sum of electronic and thermal Free Energies=" in line:
                self.sum_of_electronic_and_thermal_free_energies = float(line.split()[7])
            
            if line == "E (Thermal)             CV                S":
                line = self.file_list[j := j + 2].strip(" \t\n")
                self.vibrational_thermal_contributions = {
                    "Thermal_Energy":[],
                    "CV":[],
                    "S":[]
                }
                while line != "Q            Log10(Q)             Ln(Q)":
                    split_line = line.split()
                    if len(split_line) == 5 and split_line[0] == "Vibration" or split_line[0] == "internal" :
                        name = split_line[0]+"_" + split_line[1]
                        self.vibrational_thermal_contributions["Thermal_Energy"].append((name,float(split_line[2])))
                        self.vibrational_thermal_contributions["CV"].append((name,float(split_line[3])))
                        self.vibrational_thermal_contributions["S"].append((name,float(split_line[4])))
                    elif len(split_line) == 4:
                        
                        self.vibrational_thermal_contributions["Thermal_Energy"].append((split_line[0],float(split_line[1])))
                        self.vibrational_thermal_contributions["CV"].append((split_line[0],float(split_line[2])))
                        self.vibrational_thermal_contributions["S"].append((split_line[0],float(split_line[3])))
                    elif len(split_line) == 2 and split_line[0] == "Corrected":
                        pass
                    else:
                        print("something_went_wrong on line" + str(j) + "\n" + line)


                    line = self.file_list[j := j + 1].strip(" \t\n")

            line = self.file_list[j := j + 1].strip(" \t\n")
        self.zero_point_energy = self.sum_of_electronic_and_thermal_free_energies - self.thermal_correction_to_gibbs_free_energy
            
        self.current_index = j


