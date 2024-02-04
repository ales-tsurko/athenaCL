#!/usr/local/bin/python
# -----------------------------------------------------------------||||||||||||--
# Name:          help.py
# Purpose:       athenaCL help files.
#
# Authors:       Christopher Ariza
#
# Copyright:     (c) 2001-2010 Christopher Ariza
# License:       GPL
# -----------------------------------------------------------------||||||||||||--

import unittest, doctest


from athenaCL.libATH import language
from athenaCL.libATH import typeset
from athenaCL.libATH import drawer
from athenaCL.libATH import faq

lang = language.LangObj()
_MOD = "help.py"


class HelpDoc:
    """basic holder for help files
    names must be the same as actual commands
    names without commands will apprea as general topics
    """

    # -----------------------------------------------------------------------||--
    # define common messages shared w/ commands private variables
    _tniToggle = 'The output of this command is configured by the active system Tn/TnI mode; to change the set class Tn/TnI mode enter the command "SCmode".'

    _gfxOption = 'Output in "tk" requires the Python Tkinter GUI installation; output in "png" and "jpg" requires the Python Imaging Library (PIL) library installation; output in "eps" and "text" do not require any additional software or configuration.'

    _gfxCommand = (
        'This command uses the active graphic output format; this can be selected with the "APgfx" command. %s'
        % _gfxOption
    )

    _scratchDir = (
        "This file is written in the scratch directory specified by APdir command."
    )

    # -----------------------------------------------------------------------||--

    # this needs more explanation
    _formatMap = "MapClasses are notated in two possible notations. An index notation specifies a source:destination size pair followed by an index number. For example: 3:4-35 is the thirty fifth map class between sets of 3 and 4 elements. A spatial notation uses names and order position to code transitions. For example: (cd(ab))."

    # note: pch is supported (w/ pch label) not specified here for practicality
    _formatPitch = 'Pitches may be specified by letter name (psName), pitch space (psReal), pitch class, MIDI note number, or frequency. Pitch letter names may be specified as follows: a sharp is represented as "#"; a flat is represented as "$"; a quarter sharp is represented as "~"; multiple sharps, quarter sharps, and flats are valid. Octave numbers (where middle-C is C4) can be used with pitch letter names to provide register. Pitch space values (as well as pitch class) place C4 at 0.0. MIDI note numbers place C4 at 60. Numerical representations may encode microtones with additional decimal places. MIDI note-numbers and frequency values must contain the appropriate unit as a string ("m" or "hz").'

    _formatSieve = 'Xenakis sieves are entered using logic constructions of residual classes. Residual classes are specified by a modulus and shift, where modulus 3 at shift 1 is notated 3@1. Logical operations are notated with "&" (and), "|" (or), "^" (symmetric difference), and "-" (complementation). Residual classes and logical operators may be nested and grouped by use of braces ({}). Complementation can be applied to a single residual class or a group of residual classes. For example: -{7@0|{-5@2&-4@3}}. When entering a sieve as a pitch set, the logic string may be followed by two comma-separated pitch notations for register bounds. For example "3@2|4, c1, c4" will take the sieve between c1 and c4.'
    _formatPulse = "Pulses represent a duration value derived from ratio and a beat-duration. Beat duration is always obtained from a Texture. Pulses are noted as a list of three values: a divisor, a multiplier, and an accent. The divisor and multiplier must be positive integers greater than zero. Accent values must be between 0 and 1, where 0 is a measured silence and 1 is a fully sounding event. Accent values my alternatively be notated as + (for 1) and o (for 0). If a beat of a given duration is equal to a quarter note, a Pulse of (1,1,1) is a quarter note, equal in duration to a beat. A Pulse of (2,1,0) is an eighth-note rest: the beat is divided by two and then multiplied by one; the final zero designates a rest. A Pulse of (4,3,1) is a dotted eight note: the beat is divided by four (a sixteenth note) and then multiplied by three; the final one designates a sounding event. A Rhythm is designated as list of Pulses. For example: ((4,2,1), (4,2,1), (4,3,1))."

    _formatMarkov = 'Markov transition strings are entered using symbolic definitions and incomplete n-order weight specifications. The complete transition string consists of two parts: symbol definition and weights. Symbols are defined with alphabetic variable names, such as "a" or "b"; symbols may be numbers, strings, or other objects. Key and value pairs are notated as such: name{symbol}. Weights may be give in integers or floating point values. All transitions not specified are assumed to have equal weights. Weights are specified with key and value pairs notated as such: transition{name=weight | name=weight}. The ":" character is used as the zero-order weight key. Higher order weight keys are specified using the defined variable names separated by ":" characters. Weight values are given with the variable name followed by an "=" and the desired weight. Multiple weights are separated by the "|" character. All weights not specified, within a defined transition, are assumed to be zero. For example, the following string defines three variable names for the values .2, 5, and 8 and provides a zero order weight for b at 50%, a at 25%, and c at 25%: a{.2}b{5}c{8} :{a=1|b=2|c=1}. N-order weights can be included in a transition string. Thus, the following string adds first and second order weights to the same symbol definitions: a{.2}b{5}c{8} :{a=1|b=2|c=1} a:{c=2|a=1} c:{b=1} a:a:{a=3|b=9} c:b:{a=2|b=7|c=4}. For greater generality, weight keys may employ limited single-operator regular expressions within transitions. Operators permitted are "*" (to match all names), "-" (to not match a single name), and "|" (to match any number of names). For example, a:*:{a=3|b=9} will match "a" followed by any name; a:-b:{a=3|b=9} will match "a" followed by any name that is not "b"; a:b|c:{a=3|b=9} will match "a" followed by either "b" or "c".'

    _formatAudacity = 'Audacity frequency-analysis files can be produced with the cross-platform open-source audio editor Audacity. In Audacity, under menu View, select Plot Spectrum, configure, and export. The file must have a .txt extension. To use the file-browser, enter "import"; to select the file from the prompt, enter the complete file path, optionally followed by a comma and the number of ranked pitches to read.'

    _pitchGroups = (
        "Users may specify pitch groups in a variety of formats. A Forte set class number (6-23A), a pitch-class set (4,3,9), a pitch-space set (-3, 23.2, 14), standard pitch letter names (A, C##, E~, G#), MIDI note numbers (58m, 62m), frequency values (222hz, 1403hz), a Xenakis sieve (5&3|11), or an Audacity frequency-analysis file (import) all may be provided. "
        + _formatPitch
        + " "
        + _formatSieve
        + " "
        + _formatAudacity
    )

    # -----------------------------------------------------------------------||--
    w = "This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. http://www.fsf.org/copyleft/gpl.html"
    w_usage = "w"

    c = (
        "%s This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. See the GNU General Public License for more details. http://www.fsf.org/copyleft/gpl.html"
        % lang.msgAthCopyright
    )
    c_usage = "c"

    r = lang.msgCredits
    r_usage = "r"

    quit = "quit: Exit athenaCL."
    quit_usage = "quit"

    q = "q: Exit athenaCL."
    q_usage = "q [confirm]"

    help = 'help: To get help for a command or any available topic, enter "help" or "?" followed by a search string. If no command is provided, a menu of all commands available is displayed.'
    help_usage = "help cmd"

    py = "Begins an interactive Python session inside the current athenaCL session."
    py_usage = "py"

    shell = 'On UNIX-based platforms, the "shell" or "!" command executes a command-line argument in the default shell.'
    shell_usage = "shell cmd"

    cmd = "cmd: Displays a hierarchical menu of all athenaCL commands."
    cmd_usage = "cmd"

    pypath = "pypath: Lists all file paths in the Python search path."
    pypath_usage = "pypath"

    # -----------------------------------------------------------------------||--

    #     SCv = 'SCv: SetClass: View: Displays all data in the set class dictionary for the user-supplied pitch groups. %s For all pitch groups the SCv command interprets the values as a set class. The Normal Form, Invariance Vector and all N Class Vectors (for the active Tn/TnI mode) are displayed. N-Class Vectors, when necessary, are displayed in 20 register rows divided into two groups of 10 and divided with a dash (-). %s' % (_pitchGroups, _tniToggle)
    #     SCv_usage = 'scv set'
    #
    #     SCcm = 'SCcm: SetClass: Comparison: Compare any two user-selected pitch groups (as set classes) with all available Set Class similarity measures (SetMeasures). For each SetMeasure the calculated similarity value, a proportional graph of that value within the SetMeasure\'s range, and the measure\'s range (between minimum and maximum) are displayed.'
    #     SCcm_usage = 'scv set1 set2'
    #
    #     SCs = 'SCs: SetClass: Search: Search all set classes with the active SetMeasure for similarity to a pitch group (as a set class) and within a similarity range. The user must supply a pitch group and a percent similarity range. Similarity ranges are stated within the unit interval (between 0 and 1). To change the active SetMeasure, enter "SMo".'
    #     SCs_usage = 'scv set percentMin,percentMax'
    #
    #     SCf = 'SCf: SetClass: Find: Search all set classes with various search methods. Search methods include searching by common name (such as major, all-interval, phrygian, or pentatonic), z-relation, or superset.'
    #     SCf_usage = 'scf method argument'
    #
    #     SCmode = 'SCmode: SetClass: Mode: Sets system-wide Tn (set classes not differentiated by transposition) or Tn/I (set classes not differentiated by transposition and inversion) state for all athenaCL set class processing. To view active SCmode state, enter "AUsys".'
    #     SCmode_usage = 'scmode'
    #
    #     SCh = 'SCh: SetClass: Hear: Creates a temporary Texture with the selected set and the DroneSustain TextureModule, and uses this Texture to write a short sample EventList as a temporary MIDI file. %s If possible, this file is opened and presented to the user.' % _scratchDir
    #     SCh_usage = 'sch'
    #
    #     #-----------------------------------------------------------------------||--
    #     SMo = 'SMo: SetMeasure: Select: Sets the active SetMeasure, or computational method of set class comparison, used for "SCf", "PScpa", "PScpb" commands.'
    #     SCo_usage = 'smo name'
    #
    #     SMls = 'SMls: SetMeasure: List: Displays a list of all available SetMeasures.'
    #     SMls_usage = 'smls'
    #
    #     #-----------------------------------------------------------------------||--
    #     MCv = 'MCv: MapClass: View: Displays a listing of MapClasses for a given size class (source to destination size) and between a range of indexes. %s' % _formatMap
    #     MCv_usage = 'mcv sizeSource,sizeDestination beginMap,endMap'
    #
    #     MCcm = 'MCcm: MapClass: Comparison: Displays all possible maps and analysis data between any two sets of six or fewer members. Maps can be sorted by Joseph N. Straus\'s atonal voice-leading measures Smoothness, Uniformity, or Balance. Full analysis data is provided for each map, including vectors for each measure, displacement, offset, max, and span.'
    #     MCcm_usage = 'mccm set1 set2 analysis beginMap,endMap'
    #
    #     MCopt = 'MCopt: MapClass: Optimum: Finds an optimum voice leading and minimum distance for any two sets of six or fewer elements.'
    #     MCopt_usage = 'mcopt set1 set2'
    #
    #     MCgrid = 'MCgrid: MapClass: Grid: Creates a grid of all minimum displacements between every set class of two cardinalities. Cardinalities must be six or fewer. Note: for large cardinalities, processing time may be long. Note: values calculated between different-sized sets may not represent the shortest transitional distance.'
    #     MCgrid_usage = 'mcgrid sizeSource,sizeDestination'
    #
    #     MCnet = 'MCnet: MapClass: Network: Creates a graphical display of displacement networks between set classes.'
    #     MCnet_usage = 'mcnet sizeSource,sizeDestination'

    # -----------------------------------------------------------------------||--
    PIn = (
        "PIn: PathInstance: New: Create a new Path from user-specified pitch groups. %s"
        % _pitchGroups
    )
    PIn_usage = "pin name set1 ... setN"

    PIcp = "PIcp: PathInstance: Copy: Create a copy of a selected Path."
    PIcp_usage = "picp source target1 ... targetN"

    PIrm = "PIrm (name): PathInstance: Remove: Delete a selected Path."
    PIrm_usage = "pirm name1 ... nameN"

    PImv = "PImv: PathInstance: Move: Rename a Path, and all Texture references to that Path."
    PImv_usage = "pimv source target"

    PIals = "PIals: PathInstance: Attribute List: Displays a listing of raw attributes of the selected Path."
    PIals_usage = "pials"

    PIo = 'PIo: PathInstance: Select: Select the active Path. Used for "PIret", "PIrot", "PIslc", and "TIn".'
    PIo_usage = "pio name"

    PIv = "PIv: PathInstance: View: Displays all properties of the active Path."
    PIv_usage = "piv [name]"

    PIe = "PIe: PathInstance: Edit: Edit a single Multiset in the active Path."
    PIe_usage = "pie position set"

    PIdf = "PIdf: PathInstance: Duration Fraction: Provide a new list of duration fractions for each pitch group of the active Path. Duration fractions are proportional weightings that scale a total duration provided by a Texture. When used within a Texture, each pitch group of the Path will be sustained for this proportional duration. Values must be given in a comma-separated list, and can be percentages or real values."
    PIdf_usage = "pidf durFractionList"

    PIls = "PIls: PathInstance: List: Displays a list of all Paths."
    PIls_usage = "pils"

    PIret = "PIret: PathInstance: Retrograde: Creates a new Path from the retrograde of the active Path. All PathVoices are preserved in the new Path."
    PIret_usage = "piret name"

    PIrot = "PIrot: PathInstance: Rotation: Creates a new Path from the rotation of the active Path. Note: since a rotation creates a map not previously defined, PathVoices are not preserved in the new Path."
    PIrot_usage = "pirot name position"

    PIslc = "PIslc: PathInstance: Slice: Creates a new Path from a slice of the active Path. All PathVoices are preserved in the new Path."
    PIslc_usage = "pislc name positionStart,positionEnd"

    #     PIopt = 'PIopt: PathInstance: Optimize: Creates a new Path from a voice-leading optimization of the active Path. All pitch groups will be transposed to an optimized transposition, and a new PathVoice will be created with optimized voice leadings. Note: PathVoices are not preserved in the new Path.'
    #     PIopt_usage = 'piopt name'

    PIh = (
        "PIh: PathInstance: Hear: Creates a temporary Texture with the active Path and the active TextureModule, and uses this Texture to write a short sample EventList as a temporary MIDI file. %s If possible, this file is opened and presented to the user."
        % _scratchDir
    )
    PIh_usage = "pih"

    # -----------------------------------------------------------------------||--
    #     PScma = 'PScma: PathSet: Comparison A: Analyze the active Path as a sequence of set classes. Compare each adjacent pair of pitch groups, as set classes, using the active SetMeasure. A SetMeasure is activated with the "SMo" command.'
    #     PScma_usage = 'pscma'
    #
    #     PScmb = 'PScmb: PathSet: Comparison B: Analyze the active Path as a Sequence of set classes. Compare each set class with a reference set class, employing the active SetMeasure.'
    #     PScmb_usage = 'pscma set'
    #
    #     #-----------------------------------------------------------------------||--
    #     PVn = 'PVn: PathVoice: New: Create a new PathVoice (a collection of voice leadings) for the active Path. Each PathVoice voice leading may be selected by rank or map. Rank allows the user to select a map based on its Smoothness, Uniformity, or Balance ranking.'
    #     PVn_usage = 'pvn name map1 ... mapN'
    #
    #     PVcp = 'PVcp: PathVoice: Copy: Duplicate an existing PathVoice within the active Path. To see all PathVoices enter "PVls".'
    #     PVcp_usage = 'pvcp source target1 ... targetN'
    #
    #     PVrm = 'PVrm: PathVoice: Delete: Delete an existing PathVoice within the active Path. To see all PathVoices enter "PVls".'
    #     PVrm_usage = 'pvrm name1 ... nameN'
    #
    #     PVo = 'PVo: PathVoice: Select: Select an existing PathVoice within the active Path. To see all PathVoices enter "PVls".'
    #     PVo_usage = 'pvo name'
    #
    #     PVv = 'PVv: PathVoice: View: Displays the active Path and the active PathVoice.'
    #     PVv_usage = 'pvv [name]'
    #
    #     PVls = 'PVls: PathVoice: List: Displays a list of all PathVoices associated with the active Path.'
    #     PVls_usage = 'pvls'
    #
    #     PVan = 'PVan: PathVoice: Analysis: Displays Smoothness, Uniformity, and Balance analysis data for each map in the active PathVoice of the active Path.'
    #     PVan_usage = 'pvan'
    #
    #     PVcm = 'PVcm: PathVoice: Comparison: Displays Smoothness, Uniformity, and Balance analysis data for an ordered partition of all maps available between any two sets in the active Path.'
    #     PVcm_usage = 'pvcm positionStart,positionEnd analysis beginMap,endMap'
    #
    #     PVe = 'PVe: PathVoice: Edit: Choose a new map for a single position within the active PathVoice and Path.'
    #     PVe_usage = 'pve position map'
    #
    #     PVauto = 'PVauto: PathVoice: Auto: Create a new PathVoice with mappings chosen automatically from either the first or last ranked map of a user-selected ranking method (Smoothness, Uniformity, or Balance). A new PathVoice is created, all maps being either first or last of the particular ranking.'
    #     PVauto_usage = 'pvauto name analysis firstLast'

    # -----------------------------------------------------------------------||--

    TMo = 'TMo: TextureModule: Select: Choose the active TextureModule. This TextureModule is used with the "TIn" and "TMv" commands.'
    TMo_usage = "tmo name"

    TMv = (
        "TMv: TextureModule: View: Displays documentation for the active TextureModule."
    )
    TMv_usage = "tmv [name]"

    TMls = "TMls: TextureModule: List: Displays a list of all TextureModules."
    TMls_usage = "tmls"

    TMsd = "TMsd: TextureModule: Seed: Sets the global random seed used by all Texture Modules."
    TMsd_usage = "tmsd seed"

    # -----------------------------------------------------------------------||--

    TPls = "TPls: TextureParameter: List: Displays a list of all ParameterObjects."
    TPls_usage = "tpls"

    TPv = "TPv: TextureParameter: View: Displays documentation for one or more ParameterObjects. All ParameterObjects that match the user-supplied search string will be displayed. ParameterObject acronyms are accepted."
    TPv_usage = "tpv [name]"

    TPmap = (
        "TPmap: TextureParameter: Map: Displays a graphical map of any ParameterObject. User must supply parameter library name, the number of events to be calculated, and appropriate parameter arguments. %s"
        % _gfxCommand
    )
    TPmap_usage = "tpmap events arguments"

    # this my be incomplete
    TPe = "TPe: TextureParameter: Export: Export ParameterObject data as a file; file types available are pureDataArray, audioFile, textSpace, and textTab."
    TPe_usage = "tpe format events arguments [filePath]"

    TPsd = "TPsd: TextureParameter: Seed: Sets the global random seed used by all Texture Parameters."
    TPsd_usage = "tpsd seed"

    # -----------------------------------------------------------------------||--

    TIn = "TIn: TextureInstance: New: Creates a new instance of a Texture with a user supplied Instrument and Texture name. The new instance uses the active TextureModule, the active Path, and an Instrument selected from the active EventMode-determined Orchestra. For some Orchestras, the user must supply the number of auxiliary parameters."
    TIn_usage = "tin name instNumber"

    TIcp = "TIcp: TextureInstance: Copy: Duplicates a user-selected Texture."
    TIcp_usage = "ticp source target1 ... targetN"

    TIrm = "TIrm: TextureInstance: Remove: Deletes a user-selected Texture."
    TIrm_usage = "tirm name1 ... nameN"

    TImv = "TImv: TextureInstance: Move: Renames a Texture, and all references in existing Clones."
    TImv_usage = "timv source target"

    TIo = "TIo: TextureInstance: Select: Select the active Texture from all available Textures."
    TIo_usage = "tio name"

    TIv = "TIv: TextureInstance: View: Displays all editable attributes of the active Texture, or a Texture named with a single argument."
    TIv_usage = "tiv [name]"

    TIe = "TIe: TextureInstance: Edit: Edit a user-selected attribute of the active Texture."
    TIe_usage = "tie parameter value"

    TImode = 'TImode: TextureInstance: Mode: Set the pitch, polyphony, silence, and orcMap modes for the active Texture. The pitchMode (either "sc", "pcs", or "ps") designates which Path form is used within the Texture: "sc" designates the set class Path, which consists of non-transposed, non-redundant pitch classes; "pcs" designates the pitch class space Path, retaining set order and transposition; "ps" designates the pitch space Path, retaining order, transposition, and register.'
    TImode_usage = "timode modeType value"

    TImidi = 'TImidi: TextureInstance: MIDI: Set the MIDI program and MIDI channel of a Texture, used when a "midiFile" EventOutput is selected. Users can select from one of the 128 GM MIDI programs by name or number. MIDI channels are normally auto-assigned during event list production; manually entered channel numbers (1 through 16) will override this feature.'
    TImidi_usage = "timidi pmtrType value"

    TImute = "TImute: TextureInstance: Mute: Toggle the active Texture (or any number of Textures named with arguments) on or off. Muting a Texture prevents it from producing EventOutputs. Clones can be created from muted Textures."
    TImute_usage = "timute name1 ... nameN"

    TIls = "TIls: TextureInstance: List: Displays a list of all Textures."
    TIls_usage = "tils"

    TIdoc = "TIdoc: TextureInstance: Documentation: Displays auxiliary parameter field documentation for a Texture's instrument, as well as argument details for static and dynamic Texture parameters."
    TIpmtr_usage = "tidoc"

    TIals = (
        "TIals: TextureInstance: Attribute List: Displays raw attributes of a Texture."
    )
    TIals_usage = "tials"

    TImap = (
        "TImap: TextureInstance: Map: Displays a graphical map of the parameter values of the active Texture. With the use of two optional arguments, the TImap display can be presented in four orientations. A TImap diagram can position values on the x-axis in an equal-spaced orientation for each event (event-base), or in a time-proportional orientation, where width is relative to the time of each event (time-base). A TImap diagram can display, for each parameter, direct ParameterObject values as provided to the TextureModule (pre-TM), or the values of each parameter of each event after TextureModule processing (post-TM). %s"
        % _gfxCommand
    )
    TImap_usage = "timap [timeEvent prePost]"

    # -----------------------------------------------------------------------||--

    TEv = "TEv: TextureEnsemble: View: Displays a list of ParameterObject arguments for a single attribute of all Textures."
    TEv_usage = "tev parameter"

    TEe = "TEe: TextureEnsemble: Edit: Edit a user-selected attribute for all Textures."
    TEe_usage = "tee parameter value"

    TEmidi = "TEmidi: TextureEnsemble: MidiTempo: Edit the tempo written in a MIDI file. Where each Texture may have an independent tempo, a MIDI file has one tempo. The tempo written in the MIDI file does not effect playback, but may effect transcription into Western notation. The default tempo is 120 BPM."
    TEmidi_usage = "temidi parameter"

    TEmap = (
        "TEmap: TextureEnsemble: Map: Provides a text-based display and/or graphical display of the temporal distribution of Textures and Clones. %s"
        % _gfxCommand
    )
    TEmap_usage = "temap"

    # -----------------------------------------------------------------------||--
    TCn = "TCn: TextureClone: New: Creates a new Clone associated with the active Texture."
    TCn_usage = "tcn name"

    TCo = "TCo: TextureClone: Select: Choose the active Clone from all available Clones associated with the active Texture."
    TCo_usage = "tco name"

    TCv = "TCv: TextureClone: View: Displays all editable attributes of the active Clone, or a Clone named with a single argument."
    TCv_usage = "tcv [name]"

    TCls = "TCls: TextureClone: List: Displays a list of all Clones associated with the active Texture."
    TCls_usage = "tcls"

    TCe = "TCe: TextureClone: Edit: Edit attributes of the active Clone."
    TCe_usage = "tce parameter value"

    TCcp = "TCcp: TextureClone: Copy: Duplicates a user-selected Clone associated with the active Texture."
    TCcp_usage = "tccp source target1 ... targetN"

    TCrm = "TCrm: TextureClone: Remove: Deletes a Clone from the active Texture."
    TCrm_usage = "tcrm name1 ... nameN"

    TCmute = "TCmute: TextureClone: Mute: Toggle the active Clone (or any number of Clones named with arguments) on or off. Muting a Clone prevents it from producing EventOutputs."
    TCmute_usage = "tcmute name1 ... nameN"

    TCmap = (
        "TCmap: TextureClone: Map: Displays a graphical map of the parameter values of the active Clone. With the use of one optional argument, the TCmap display can be presented in two orientations. A TCmap diagram can position values on the x-axis in an equal-spaced orientation for each event (event-base), or in a time-proportional orientation, where width is relative to the time of each event (time-base). As Clones process values produced by a Texture, all TCmap displays are post-TM. %s"
        % _gfxCommand
    )
    TCmap_usage = "tcmap [timeEvent]"

    TCdoc = "TCdoc: TextureClone: Documentation: Displays documentation for each auxiliary parameter field from the associated Texture, as well as argument formats for static Clone options."
    TIpmtr_usage = "tidoc"

    TCals = "TCals: TextureClone: Attribute List: Displays raw attributes of the active Clone."
    TCals_usage = "tcals"

    # -----------------------------------------------------------------------||--
    TTls = (
        "TTls: TextureTemperament: List: Displays a list of all temperaments available."
    )
    TTls_usage = "ttls"

    TTo = "TTo: TextureTemperament: Select: Choose a Temperament for the active Texture. The Temperament provides fixed or dynamic mapping of pitch values. Fixed mappings emulate historical Temperaments, such as MeanTone and Pythagorean; dynamic mappings provide algorithmic variation to each pitch processed, such as microtonal noise."
    TTo_usage = "tco name"

    # -----------------------------------------------------------------------||--
    EOls = "EOls: EventOutput: List: List all available EventOutput formats."
    EOls_usage = "eols"

    EOo = "EOo: EventOutput: Select: Adds a possible output format to be produced when an event list is created. Possible formats are listed with EOls."
    EOo_usage = "eoo format"

    EOrm = "EOrm: EventOutput: Remove: Removes a possible output format to be produced when an event list is created. Possible formats can be seen with EOls."
    EOrm_usage = "eorm format"

    # -----------------------------------------------------------------------||--
    EMls = "EMls: EventMode: List: Displays a list of available EventModes."
    EMls_usage = "EMls"

    EMo = "EMo: EventMode: Select: Select an EventMode. EventModes determine what instruments are available for Textures, default auxiliary parameters for Textures, and the final output format of created event lists."
    EMo_usage = "emo name"

    EMv = "EMv: EventMode: View: Displays documentation for the active EventMode. Based on EventMode and selected EventOutputs, documentation for each active OutputEngine used to process events is displayed."
    EMv_usage = "emv"

    EMi = "EMi: EventMode: Instruments: Displays a list of all instruments available as defined within the active EventMode. The instrument assigned to a Texture determines the number of auxiliary parameters and the default values of these parameters."
    EMi_usage = "emi"

    # -----------------------------------------------------------------------||--
    ELn = "ELn: EventList: New: Create a new event list, in whatever formats are specified within the active EventMode and EventOutput. Generates new events for all Textures and Clones that are not muted. Specific output formats are determined by the active EventMode (EMo) and selected output formats (EOo)."
    ELn_usage = "eln filename.xml"

    ELw = "ELw: EventList: Save: Write event lists stored in Textures and Clones, in whatever formats specified within the active EventMode and EventOutput; new event lists are not generated, and output will always be identical."
    ELw_usage = "elw filename.xml"

    ELv = "ELv: EventList: View: Opens the last event list created in the current session as a text document."
    ELv_usage = "elv"

    ELh = "ELh: EventList: Hear: If possible, opens and presents to the user the last audible EventList output (audio file, MIDI file) created in the current session."
    ELh_usage = "elh"

    ELr = "ELr: EventList: Render: Renders the last event list created in the current session with the Csound application specified by APea."
    ELr_usage = "elr"

    ELauto = "ELauto: EventList: Auto Render Control: Turn on or off auto rendering, causing athenaCL to automatically render (ELr) and hear (ELh) whenever an event list is created with ELn."
    ELauto_usage = "elauto"

    # -----------------------------------------------------------------------||--
    AOw = "AOw: AthenaObject: Save: Saves an AthenaObject file, containing all Paths, Textures, Clones, and environment settings."
    AOw_usage = "aow filename.xml"

    AOl = "AOl: AthenaObject: Load: Load an athenaCL XML AthenaObject. Loading an AthenaObject will overwrite any objects in the current AthenaObject."
    AOl_usage = "aol filename.xml"

    AOmg = "AOmg: AthenaObject: Merge: Merges a selected XML AthenaObject with the current AthenaObject."
    AOmg_usage = "aomg filename.xml"

    AOrm = "AOrm: AthenaObject: Remove: Reinitialize the AthenaObject, destroying all Paths, Textures, and Clones."
    AOrm_usage = "aorm [confirm]"

    AOals = "AOals: AthenaObject: Attribute List: Displays raw attributes of the current AthenaObject."
    AOals_usage = "aoals"

    # -----------------------------------------------------------------------||--

    APcurs = "APcurs: AthenaPreferences: Cursor: Toggle between showing or hiding the cursor prompt tool."
    APcurs_usage = "apcurs"

    APr = "APr: AthenaPreferences: Refresh: When refresh mode is active, every time a Texture or Clone is edited, a new event list is calculated in order to test ParameterObject compatibility and to find absolute time range. When refresh mode is inactive, editing Textures and Clones does not test event list production, and is thus significantly faster."
    APr_usage = "apr"

    APwid = "APwid: AthenaPreferences: Width: Manually set the number of characters displayed per line during an athenaCL session. Use of this preference is only necessary on platforms that do not provide a full-featured terminal envrionment."
    APwid_usage = "apwid characterWidth"

    APdlg = 'APdlg: AthenaPreferences: Dialogs: Toggle between different dialog modes. Not all modes are available on every platform or Python installation. The "text" dialog mode works without a GUI, and is thus available on all platforms and Python installations.'
    APdlg_usage = "apdlg dialogMode"

    APgfx = (
        "APgfx: AthenaPreferences: Graphics: Toggle between different graphic output formats. All modes may not be available on every platform or Python installation. %s"
        % _gfxCommand
    )
    APgfx_usage = "apgfx dialogMode"

    APdir = 'APdir: AthenaPreferences: Directories: Lets the user select or enter directories necessary for writing and searching files. Directories that can be entered are the "scratch" directory and the "user audio". The scratch directory is used for writing temporary files with automatically-generated file names. Commands such as SCh, PIh, and those that produce graphics (depending on format settings specified with APgfx) use this directory. The user audio directory is used within ParameterObjects that search for files. With such ParameterObjects, the user can specify any file within the specified directory simply by name. To find the the file\'s complete file path, all directories are recursively searched in both the user audio and the athenaCL/audio directories. Directories named "_exclude" will not be searched. If files in different nested directories do not have unique file names, correct file paths may not be found.'
    APdir_usage = "apdir dirType filePath"

    #     APcc = 'APcc: AthenaPreferences: Customize Cursor: Lets the user customize the cursor prompt tool by replacing any of the standard characters with any string. The user may optionally select to restore system defaults.'
    #     APcc_usage = 'apcc "[" "]" "(" ")" "PI" "TI"'

    APea = "APea: AthenaPreferences: External Applications: Set the file path to external utility applications used by athenaCL. External applications can be set for Csound (csoundCommand) and for handling various media files: midi (midiPlayer), audio (audioPlayer), text (textReader), image (imageViewer), and postscript (psViewer)."
    APea_usage = "apea appType filePath"

    #     CPff = 'CPff: CsoundPreferences: FileFormat: Choose which audio file format (AIF, WAVE, or SoundDesignerII) is created by Csound.'
    #     CPff_usage = 'cpff format'
    #
    #     CPch = 'CPch: CsoundPreferences: Channels: Choose the number of audio channels used in creating the Csound orchestra. Channel options are mono, stereo, and quad (1, 2, and 4 channels).'
    #     CPch_usage = 'cpch channels'
    #

    APa = "APa: AthenaPreferences: Audio: Set audio preferences."
    APa_usage = "apa type value"

    # -----------------------------------------------------------------------||--

    AHls = "AHls: AthenaHistory: List: Displays a listing of the current history."
    AHls_usage = "ahls"

    AHrm = "AHrm: AthenaHistory: Remove: Deletes the stored command history."
    AHrm_usage = "ahrm"

    AHexe = "AHexe: AthenaHistory: Execute: Execute a command or a command range within the current history."
    AHexe_usage = "ahexe cmdRange"

    # -----------------------------------------------------------------------||--

    #     ASexe = 'ASexe: AthenaScript: Execute: Runs an AthenaScript if found in the libATH/libAS directory. Not for general use.'
    #     ASexe_usage = 'asexe [scriptName]'

    # -----------------------------------------------------------------------||--

    AUbeat = "AUbeat: AthenaUtility: Beat: Simple tool to calculate the duration of a beat in BPM."
    AUbeat_usage = "aubeat"

    AUlog = "AUlog: AthenaUtility: Log: If available, opens the athenacl-log file used to store error messages."
    AUlog_usage = "aulog"

    AUpc = (
        "AUpc: AthenaUtility: Pitch Converter: Enter a pitch, pitch name, or frequency value to display the pitch converted to all formats. %s"
        % _formatPitch
    )
    AUpc_usage = "aupc pitch"

    AUsys = "AUsys: AthenaUtility: System: Displays a list of all athenaCL properties and their current status."
    AUsys_usage = "ausys"

    AUdoc = "AUdoc: AthenaUtility: Documentation: Opens the athenaCL documentation in a web browser. Attempts to load documentation from a local copy; if this fails, the on-line version is loaded."
    AUdoc_usage = "audoc"

    AUup = "AUup: AthenaUtility: Update: Checks on-line to see if a new version of athenaCL is available; if so, the athenaCL download page will be opened in a web browser."
    AUup_usage = "auup"

    # this command is hidden
    AUbug = (
        "AUbug: AthenaUtility: Bug: causes a bug to test the error reporting system."
    )
    AUbug_usage = "aubug"

    # markov utilites
    AUmg = (
        "AUmg: AthenaUtility: Markov Generator: Given a properly formated Markov transition string, this command generates a number of values as specified by the count argument. %s"
        % _formatMarkov
    )
    AUmg_usage = "aumg count order transition"

    AUma = "AUma: AthenaUtility: Markov Analysis: Given a desired maximum order, this command analyzes the the provided sequence of any space delimited values and returns a Markov transition string."
    AUma_usage = "auma order sequence"

    AUca = "AUca: AthenaUtility: Cellular Automata: Utility for producing visual representations of values generated by various one-dimensional cellular automata."
    AUca_usage = "auca spec rule mutation"

    # -----------------------------------------------------------------------||--
    #     SC = 'SetClass: Commands: Displays a list of all SetClass dictionary commands.'
    #     SC_usage = 'sc'
    #     MC = 'MapClass: Commands: Displays a list of all MapClass dictionary commands.'
    #     MC_usage = 'mc'
    #
    #     SM = 'SetMeasure: Commands: Displays a list of all SetMeasure dictionary commands.'
    #     SM_usage = 'sm'

    PI = "PathInstance: Commands: Displays a list of all PathInstance commands."
    PI_usage = "pi"

    #     PS = 'PathSet: Commands: Displays a list of all PathSet commands.'
    #     PS_usage = 'ps'
    #     PV = 'PathVoice: Commands: Displays a list of all PathVoice commands.'
    #     PV_usage = 'pv'

    TM = "TextureModule: Commands: Displays a list of all TextureModule commands."
    TM_usage = "tm"

    TP = "TextureParameter: Commands: Displays a list of all TextureParameter commands."
    TP_usage = "tp"

    TI = "TextureInstance: Commands: Displays a list of all TextureInstance commands."
    TI_usage = "ti"
    TC = "TextureClone: Commands: Displays a list of all TextureClone commands."
    TC_usage = "tc"
    TT = "TextureTemperament: Commands: Displays a list of all TextureTemperament commands."
    TT_usage = "tt"
    TE = "TextureEnsemble: Commands: Displays a list of all TextureEnsemble commands."
    TE_usage = "te"

    EL = "EventList: Commands: Displays a list of all EventList commands."
    EL_usage = "el"
    EM = "EventMode: Commands: Displays a list of all EventMode commands."
    EM_usage = "em"
    EO = "EventOutput: Commands: Displays a list of all EventOutput commands."
    EO_usage = "eo"

    #     CP = 'CsoundPreferences: Commands: Displays a list of all CsoundPreferences commands.'
    #     CP_usage = 'cp'

    AO = "AthenaObject: Commands: Displays a list of all AthenaObject commands."
    AO_usage = "ao"
    AP = "AthenaPreferences: Commands: Displays a list of all AthenaPreferences commands."
    AP_usage = "ap"
    AH = "AthenaHistory: Commands: Displays a list of all AthenaHistory commands."
    AH_usage = "ah"
    AU = "AthenaUtility: Commands: Displays a list of all AthenaUtility commands."
    AU_usage = "au"

    # -----------------------------------------------------------------------||--

    def __init__(self, termObj=None):

        # list of attribute names to always exclude
        # all double underscores will always be excluded
        self.__exclude = [
            "listCmdDoc",
            "searchCmdDoc",
            "searchCmdUsage",
            "searchRef",
            "reprUsage",
            "reprCmd",
            "termObj",
            "faqObj",
        ]
        # provide a dictionary of terms for glossary lookup
        # used in AUref command
        # this is treated as a private variable to avoid being presented
        # as a help topic
        self.__glossIndex = {
            #         '_formatMap' : {'title': 'MapClass',
            #                'syn': ['mapclass', 'maping', 'straus', 'voiceleading']},
            "_formatSieve": {"title": "Xenakis Sieves", "syn": ["xenakis", "sieve"]},
            "_formatPitch": {
                "title": "Pitch Formats",
                "syn": ["pc", "notes", "pitches", "fq"],
            },
            "_formatMarkov": {
                "title": "Markov Notation",
                "syn": ["transition", "markov"],
            },
            "_formatAudacity": {
                "title": "Audacity Files",
                "syn": ["spectrum", "frequency analysis", "fq"],
            },
            "_pitchGroups": {
                "title": "Pitch Groups",
                "syn": ["set", "sieve", "groups", "forte", "setclass"],
            },
            "_formatPulse": {
                "title": "Pulse and Rhythm",
                "syn": ["pulse", "rhythm", "beat", "groove", "duration"],
            },
            "r": {"title": "Credits", "syn": ["credits", "copyright", "athena"]},
            "c": {
                "title": "Copyright",
                "syn": ["distribution", "copyright", "gpl", "open source", "distro"],
            },
            "w": {"title": "Warranty", "syn": ["warranty", "merchantability"]},
        }

        self.__msgUsage = "usage:"
        # this objects are excluded above
        self.termObj = termObj
        self.faqObj = faq.FaqDictionary()

    def __listAttr(self):
        """list of raw attributes that have doc data
        exclude internal methods and other things"""
        attr = dir(self)  # already sorted
        filter = []
        for name in attr:
            if name[:2] == "__":
                pass
            elif name[:10] == "_HelpDoc__":
                pass  # used to mask private attr
            elif name in self.__exclude:
                pass
            else:
                filter.append(name)
        return filter

    # -----------------------------------------------------------------------||--
    def listCmdDoc(self):
        """provide a list of command documentation topics
        this includes only topics that do not start with an underscore
        """
        attr = self.__listAttr()
        filter = []
        for name in attr:
            if name[:1] == "_":
                pass
            elif name[-6:] == "_usage":
                pass
            else:
                filter.append(name)
        return filter

    def searchCmdDoc(self, searchStr):
        """search all available information for matching entries
        returns corrected attr name, as well as doc str"""
        attr = self.listCmdDoc()
        for name in attr:
            if name.lower() == searchStr.lower():
                return name, getattr(self, name)
        return None, None  # return none if fails

    def searchCmdUsage(self, searchStr):
        """search for usage string, where searchStr is the name of the command
        returns corrected attr name, as well as doc str
        """
        attr = self.__listAttr()
        for name in attr:
            if name.lower() == searchStr.lower() + "_usage":
                return name, getattr(self, name)
        return None, None

    def searchRef(self, searchStr):
        """search all help topics for all references topics
        returns a list of ordered pairs, attr name, doc Str"""
        filter = []
        attr = self.__listAttr()
        for name in attr:
            if searchStr.lower() in name.lower():
                doc = getattr(self, name)
                filter.append([name, doc])
            # if in gloss, search for synonymes
            elif name in list(self.__glossIndex.keys()):
                for altName in self.__glossIndex[name]["syn"]:
                    if searchStr in altName or altName in searchStr:
                        doc = getattr(self, name)
                        filter.append([name, doc])
                        break

        return filter

    # -----------------------------------------------------------------------||--
    def reprUsage(self, searchStr, errorStr=None):
        """just return a formatted usage string, or error message if none
        exists; this is used as an error message from command.py when bad command
        line args are given"""
        name, usageStr = self.searchCmdUsage(searchStr)
        if usageStr == None:
            if errorStr == None:
                return "incorrect usage; no additional help available.\n"
            else:
                return "incorrect usage; %s.\n" % errorStr
        elif errorStr == None:
            return "%s %s\n" % (self.__msgUsage, usageStr)
        else:
            if not drawer.isStr(errorStr):  # case of an built-in exception obj
                errorStr = str(errorStr)  # must be converted into string
            errorStr = errorStr.strip()
            # this used to replace colons w/ periods,
            # but this is not always desirable
            # errorStr = errorStr.replace(':', '.')
            return "%s %s (%s)\n" % (self.__msgUsage, usageStr, errorStr)

    def reprCmd(self, searchStr):
        """main public interface called from Command object to get
        documentation"""
        entryLines = []

        cmdName, docStr = self.searchCmdDoc(searchStr)
        usageName, usageStr = self.searchCmdUsage(searchStr)

        if docStr != None:
            entryLines.append((cmdName, docStr))
            if usageStr != None:
                entryLines.append((self.__msgUsage, usageStr))

        if entryLines == []:  # if nothing found
            # this searches all attributes of help, all gloss and synonym entries
            filter = self.searchRef(searchStr)
            for name, doc in filter:
                if name in list(self.__glossIndex.keys()):
                    title = self.__glossIndex[name]["title"]
                # alter usage attributes with a predictable title
                # will add usage documentation to command documentation
                elif name[-6:] == "_usage":
                    cmdName = name[:-6]
                    title = "%s %s" % (cmdName, self.__msgUsage)
                else:
                    if name[0] == "_":  # remove leading underscore
                        title = name[1:]
                    else:
                        title = name
                entryLines.append((title, doc))
        # last attempt: search faq questions
        if entryLines == []:
            q, a = self.faqObj.searchQuery(searchStr)
            if q != None:
                entryLines.append(("frequently asked", "%s %s" % (q, a)))

        if entryLines == []:  # still empty
            return 'no help for: "%s"\n' % searchStr

        msg = []
        headerKey = ["topic", "documentation"]
        minWidthList = (lang.LMARGINW, 0)
        bufList = [1, 1]
        justList = ["l", "l"]
        table = typeset.formatVariCol(
            headerKey,
            entryLines,
            minWidthList,
            bufList,
            justList,
            self.termObj,
            "oneColumn",
        )
        msg.append("%s\n" % table)

        return "".join(msg)


# -----------------------------------------------------------------||||||||||||--
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testDummy(self):
        self.assertEqual(True, True)

    def testBasic(self):
        a = HelpDoc()
        for cmd in a.listCmdDoc():  # get all commands
            post = a.reprUsage(cmd)
            post = a.reprCmd(cmd)
            post = a.searchRef(cmd)


# -----------------------------------------------------------------||||||||||||--
if __name__ == "__main__":
    from athenaCL.test import baseTest

    baseTest.main(Test)
