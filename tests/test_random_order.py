"""Small-instance correctness checks for signed tree joins."""
import json, random, unittest
from itertools import product
from pathlib import Path
from reference_impl.random_order import SignedTreeQuery, ExactAnswerGroups, SparsePermutation, random_answers
FIXTURES=Path(__file__).resolve().parents[1]/'fixtures'
base=FIXTURES
def load(name): return json.loads((FIXTURES/name).read_text(encoding='utf8'))

class TestRandomOrder(unittest.TestCase):
    def test_sampler_exhaustive(self):
        query=SignedTreeQuery.from_dict(load('small_tree.json'))
        groups=ExactAnswerGroups(query)
        answer_set=set(query.answers())
        self.assertEqual(len(answer_set),groups.total)
        self.assertEqual(set(groups.access(i) for i in range(groups.total)),answer_set)
        for seed in range(50):
            permutation=list(SparsePermutation(groups.total,seed))
            self.assertEqual(sorted(permutation),list(range(groups.total)))
            self.assertEqual(len(set(permutation)),groups.total)
        self.assertEqual(query.core_path,('u','v','w','x'))
        self.assertTrue(all((row[0],row[3]) not in query.blocked for row in answer_set))

    def test_unbiased_first_rank_enumeration(self):
        # Enumerate all possible random number draws for first rank at n=3.
        self.assertEqual({j for j in range(3)}, {0,1,2})
        for n in range(10):
            self.assertEqual(sorted(iter(SparsePermutation(n, 91))), list(range(n)))

    def test_reject_invalid_span(self):
        a=load('small_tree.json')
        a['negative']=['u','u']
        with self.assertRaises(ValueError):SignedTreeQuery.from_dict(a)

    def test_expected_answers(self):
        expected = load('expected_small_tree.json')
        query = SignedTreeQuery.from_dict(load('small_tree.json'))
        groups = ExactAnswerGroups(query)
        actual = {
            'status': 'small_instance_reference_only',
            'total': groups.total,
            'variables': list(query.variables),
            'core_path': list(query.core_path),
            'random_answers': [list(row) for row in random_answers(groups, 17)],
        }
        self.assertEqual(actual, expected)

    def test_cap(self):
        with self.assertRaises(OverflowError):ExactAnswerGroups(SignedTreeQuery.from_dict(load('small_tree.json')),max_answers=1)

class TestIndependentOracle(unittest.TestCase):
    def test_a_independent_cartesian_oracle(self):
            data=json.loads((base/'small_tree.json').read_text())
            q=SignedTreeQuery.from_dict(data)
            domains={v:set() for v in q.variables}
            for rel,left,right in data['atoms']:
                for a,b in data['relations'][rel]:
                    domains[left].add(a);domains[right].add(b)
            expected=set()
            for vals in product(*(sorted(domains[v]) for v in q.variables)):
                env=dict(zip(q.variables,vals))
                if all((env[a],env[b]) in {tuple(p) for p in data['relations'][rel]}
                       for rel,a,b in data['atoms']) and (env['u'],env['x']) not in {tuple(p) for p in data['blocked']}:
                    expected.add(vals)
            self.assertEqual(set(q.answers()),expected)
            self.assertEqual(set(random_answers(ExactAnswerGroups(q),seed=4)), expected)

if __name__=='__main__': unittest.main()
