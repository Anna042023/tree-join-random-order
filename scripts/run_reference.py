"""Print the random-order enumeration for one signed tree query."""
import argparse, json
from pathlib import Path
from reference_impl.random_order import SignedTreeQuery, ExactAnswerGroups, random_answers

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,default=Path('fixtures/small_tree.json'))
    parser.add_argument('--seed',type=int,default=17)
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding='utf8'))
    q=SignedTreeQuery.from_dict(data)
    group=ExactAnswerGroups(q,max_answers=100000)
    out=dict(status='small_instance_reference_only',total=group.total,variables=q.variables,core_path=q.core_path,random_answers=list(random_answers(group,args.seed)))
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
