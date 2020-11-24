import math
import operator
import string
import sys
from collections import OrderedDict, defaultdict

# VARIABLE_MAP = defaultdict(int)
class VariableStack(object):
    def __init__(self):
        self.map = {}
    def reset(self, reset_map=None):
        self.map = reset_map if reset_map else {}
    def __contains__(self, key):
        return key in self.map
    def __getitem__(self, key):
        return self.map[key][-1]
    def __setitem__(self, key, val):
        if key in self.map:
            self.map[key][-1] = val
        else:
            self.map[key] = [val]
    def push(self, key):
        self.map[key].append(None)
    def pop(self, key):
        self.map[key].pop(-1)


VARIABLE_MAP = VariableStack()

ON_STAGE = set()

TERMINATORS = ['.', '!', '?', ']']
def parse_txt(filename):
    return [word.strip() for word in open(filename).readlines()]
POSITIVE_NOUNS = parse_txt("words/positive_nouns.txt")
NEUTRAL_NOUNS = parse_txt("words/neutral_nouns.txt")
NEGATIVE_NOUNS = parse_txt("words/negative_nouns.txt")
POSITIVE_ADJECTIVES = parse_txt("words/positive_adjs.txt")
NEGATIVE_ADJECTIVES = parse_txt("words/negative_adjs.txt")
YOU_WORDS = ["you", "thee", "yourself", "thyself", "thou"]
ME_WORDS = ["me", "myself", "i"]


class GoToException(Exception):
    def __init__(self, destination):
        self.destination = destination
        super()


def say_output(output):
    print(output, end='')
    # print(ord(output), "[", spoken_to, "]")

def clean_line(line):
    line = line.lower().replace("\n", " ")
    return "".join(
        letter
        for letter in line
        if letter
        in string.ascii_lowercase + " -"
    )

def find_first(string, chars):
    for index, ch in enumerate(string):
        if ch in chars:
            return ch, index
    return None, -1

def convert_scene_to_sentences(lines):
    joined_line = " ".join([" ".join(line.split()) for line in lines])

    sentences = []
    while joined_line:
        ch, index = find_first(joined_line, TERMINATORS)
        if not ch: break
        sentence = joined_line[:index+1]
        joined_line = joined_line[index+1:].strip()
        sentences.append(sentence.strip())
    return sentences

def main(*args):
    source_code_lines = open(args[1]).readlines()
    groups = []
    add_to_existing_group = False
    for line in source_code_lines:
        clean_line = line.strip().lower()

        if add_to_existing_group:
            if clean_line:
                groups[-1] += "\n" + clean_line
            else:
                add_to_existing_group = False
        elif clean_line:
            groups.append(clean_line)
            add_to_existing_group = True
    title = groups.pop(0)
    variables_paragraph = groups.pop(0)

    def parse_variables(variables):
        return [variable.split(",", 1)[0] for variable in variables.splitlines()]

    variables = parse_variables(variables_paragraph)
    for variable in variables:
        VARIABLE_MAP[variable] = 0

    acts = OrderedDict()
    for line in groups:
        clean_line = line.strip()
        if clean_line.startswith("act "):
            acts[clean_line.split(": ")[0]] = OrderedDict()
        elif clean_line.startswith("scene "):
            last_act_number = list(acts.keys())[-1]
            acts[last_act_number][clean_line.split(": ")[0]] = []
        else:
            last_act_number = list(acts.keys())[-1]
            last_scene_number = list(acts[last_act_number].keys())[-1]
            acts[last_act_number][last_scene_number].append(clean_line)

    skip_to_scene = None
    for act_num, act in acts.items():
        while True:
            try:
                go_through_scenes(act, skip_to_scene)
            except GoToException as exc:
                destination = exc.destination.strip(".")
                if destination.startswith("scene"):
                    # print("skip to scene", destination)
                    skip_to_scene = destination
                    continue
                else:
                    import pdb;pdb.set_trace()
            break

def go_through_scenes(act, skip_to_scene=None):
    for scene_num, scene in act.items():
        if skip_to_scene:
            if scene_num == skip_to_scene:
                skip_to_scene = None
            else:
                continue
        sentences = convert_scene_to_sentences(scene)
        parse_scene(sentences)


def parse_characters_from_direction(direction):
    return {
        word for word
        in direction[1:-1].split()  # Strip out [ and ]
        if word not in ["enter", "exit", "exeunt", "and", "the"]
    }

def parse_question(sentence, speaker, spoken_to):
    # print("found a Q:", sentence)
    if " than " in sentence:
        part1, part2 = sentence.split(" than ")
        return (
            parse_expression(part1, speaker, spoken_to) >
            parse_expression(part2, speaker, spoken_to)
        )
    elif " as " in sentence:
        part1, _, part2 = sentence.split(" as ", 2)
        return (
            parse_expression(part1, speaker, spoken_to) ==
            parse_expression(part2, speaker, spoken_to)
        )
    else:
        import pdb;pdb.set_trace()

def parse_scene(sentences):
    global ON_STAGE

    speaker = None
    last_question_true = False
    for sentence in sentences:
        if not sentence:
            continue
        elif sentence.startswith("[enter"):
            ON_STAGE.update(parse_characters_from_direction(sentence))
            continue
        elif sentence.startswith("[exit") or sentence.startswith("[exeunt"):
            ON_STAGE -= parse_characters_from_direction(sentence)
            continue
        elif ":" in sentence:
            speaker, sentence = sentence.split(":")
            sentence = sentence.strip()

        spoken_to = list(ON_STAGE - {speaker})[0]
        cleaned_line = clean_line(sentence)

        if last_question_true:
            goto = sentence.split("if so, let us proceed to ")[1]
            last_question_true = False
            raise GoToException(goto)

        if sentence.startswith('let us return to'):
            raise GoToException(sentence.split("let us return to ", 1)[1])

        if sentence.endswith("?"):
            last_question_true = parse_question(cleaned_line, speaker, spoken_to)
            continue
        for you_word in YOU_WORDS:
            if cleaned_line.startswith(you_word):
                cleaned_line = cleaned_line[len(you_word):]
                # TODO this means we are assigning you. Check later for self assignment
                break
        result = parse_expression(cleaned_line, speaker, spoken_to)
        if result:
            # print("Setting", spoken_to, result)
            # if spoken_to == "romeo":
            #     import pdb;pdb.set_trace()
            VARIABLE_MAP[spoken_to] = result


def parse_expression(expression, speaker, spoken_to):
    copy_exp = expression

    if expression.count(" as ") > 1:
        expression = expression.split(" as ", 2)[2]
    if expression in ["speak your mind", "speak thy mind"]:
        say_output(chr(VARIABLE_MAP[spoken_to]))
        return
    if expression in ["open your heart"]:
        say_output(VARIABLE_MAP[spoken_to])
        return
    if expression in ["listen to your heart", "open your mind"]:
        if "heart" in expression:  # Number
            return int(input())
        else:  # Letter
            return input()
    if expression.startswith("remember "):
        expression = expression.split("remember ", 1)[1]
        if expression in YOU_WORDS:
            VARIABLE_MAP.push(speaker)
        elif expression in ME_WORDS:
            VARIABLE_MAP.push(spoken_to)
        else:
            import pdb;pdb.set_trace()

    if expression in YOU_WORDS:
        try:
            return VARIABLE_MAP[spoken_to]
        except KeyError:
            import pdb;pdb.set_trace()

    def split_for_expression(diffs):
        indexes = []
        for word in OPERATOR_MAP:
            if word in diffs:
                indexes.append(diffs.find(word))
        if indexes:
            left_split = diffs.find(" and ") < min(indexes)
        else:
            left_split = True

        if left_split:
            return diffs.split(" and ", 1)
        else:
            return diffs.rsplit(" and ", 1)

    OPERATOR_MAP = {
        "sum": operator.add,
        "difference": operator.sub,
        "product": operator.mul,
        "quotient": operator.floordiv,
        "remainder": operator.mod,
        "twice": lambda x, y: 2 * x,
        "square": lambda x, y: x**2,
        "square root": lambda x, y: math.sqrt(x),
        "cube": lambda x, y: x**3,
    }
    nouns = []
    for word in expression.split():
        if word in OPERATOR_MAP:
            diffs = expression.split(word + " ", 1)[1]
            if word == "remainder":
                part1, part2 = diffs.split("of the quotient", 1)[1].split(" and ")
            elif word in ["twice", "square", "cube"]:
                if "square " in expression and expression.split("square ", 1)[1].startswith("root"):
                    word = "square root"
                    diffs = expression.split("square root ", 1)[1]
                part1 = part2 = diffs
            else:
                part1, part2 = split_for_expression(diffs)
            operator_func = OPERATOR_MAP[word]
            return operator_func(
                parse_expression(part1, speaker, spoken_to),
                parse_expression(part2, speaker, spoken_to)
            )

        if word in ME_WORDS:
            nouns.append((word, VARIABLE_MAP[speaker]))
        if word in YOU_WORDS:
            nouns.append((word, VARIABLE_MAP[spoken_to]))
        if word in VARIABLE_MAP:
            nouns.append((word, VARIABLE_MAP[word]))
        if word in POSITIVE_NOUNS or word in NEUTRAL_NOUNS:
            nouns.append((word, 1))
        if word in NEGATIVE_NOUNS:
            nouns.append((word, -1))

    count = 0
    for noun, base_multiplier in nouns:
        current_line, expression = expression.split(noun, 1)
        try:
            count += calculate_adjectives(current_line, base_multiplier)
        except Exception as exc:
            import pdb;pdb.set_trace()
            foo = "bar"
    # print("\tend expression", copy_exp, count)
    return count


def calculate_adjectives(subsentence, starting_number):
    count = starting_number
    for word in subsentence.split():
        if word in NEGATIVE_ADJECTIVES + POSITIVE_ADJECTIVES:
            count *= 2
    return count

if __name__ == "__main__":
    main(*sys.argv)
