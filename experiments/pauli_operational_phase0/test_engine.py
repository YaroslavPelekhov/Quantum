import unittest
import numpy as np
from threadpoolctl import threadpool_limits
import engine as e


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.threads = threadpool_limits(limits=1)

    @classmethod
    def tearDownClass(cls):
        cls.threads.restore_original_limits()

    def state(self, q, seed=7):
        rng = np.random.default_rng(seed)
        x = rng.normal(size=1<<q)+1j*rng.normal(size=1<<q)
        return x/np.linalg.norm(x)

    def test_pauli_bit_order(self):
        labels, q = e.word_labels(['XII', 'IXI', 'IIX', 'YZY'])
        self.assertEqual(labels[:3], [(4,0),(2,0),(1,0)])
        psi = self.state(q)
        a, _ = e.moments(e.operators(labels,q),psi)
        b = e.density_expectations(np.outer(psi,psi.conj()),labels)
        np.testing.assert_allclose(a,b,atol=1e-12)

    def test_frames(self):
        s = e.system('G8')
        for k in range(3):
            labels,_ = e.frame(s['labels'],s['qubits'],k)
            self.assertEqual(e.edges_for(labels), e.edges_for(s['labels']))

    def test_channels_all_paulis(self):
        labels = [(x,z) for x in range(8) for z in range(8)]
        psi = self.state(3)
        for channel in ('none','depolarizing','amplitude_damping'):
            for p in (0,.03,.7,1.):
                a,_ = e.moments(e.operators(labels,3,channel,p),psi)
                b = e.density_expectations(e.density_channel(psi,3,channel,p),labels)
                np.testing.assert_allclose(a,b,atol=1e-11)

    def test_damping_excited_endpoint(self):
        rho = e.density_channel(np.array([0,1],complex),1,'amplitude_damping',1.)
        np.testing.assert_allclose(rho,[[1,0],[0,0]])

    def test_depolarizing_endpoint(self):
        rho = e.density_channel(self.state(3),3,'depolarizing',1.)
        np.testing.assert_allclose(rho,np.eye(8)/8,atol=1e-12)

    def test_gradients(self):
        s=e.system('G8'); ops=e.operators(s['labels'],s['qubits'],'amplitude_damping',.03)
        psi=self.state(3); raw=np.r_[psi.real,psi.imag]; w=np.array(s['weights'])
        for score in (False,True):
            value,g=e.score_and_gradient(raw,ops,w,s['bound'],score)
            for k in range(len(raw)):
                plus=raw.copy();minus=raw.copy();plus[k]+=1e-6;minus[k]-=1e-6
                numerical=(e.score_and_gradient(plus,ops,w,s['bound'],score)[0]-
                           e.score_and_gradient(minus,ops,w,s['bound'],score)[0])/2e-6
                self.assertAlmostEqual(g[k],numerical,places=6)

    def test_positive_saved_state(self):
        old=e.load('almost_clique_closure_counterexample.json')
        psi=np.array(old['integer_state_real'])+1j*np.array(old['integer_state_imag'])
        psi=psi/np.linalg.norm(psi)
        # The old state's ordering is explicitly matched to its Pauli words.
        s=e.system('G8'); mu=e.density_expectations(np.outer(psi,psi.conj()),s['labels'])
        self.assertGreater(np.array(s['weights'])@mu**2,3.03)

    def test_budget_allocation(self):
        for mu in ([0.,0.,0.],[1.,-1.,.2],[.1,.6,.9]):
            for budget in (6,7,10000):
                n=e.allocation(mu,[1,2,1],budget)
                self.assertEqual(n.sum(),budget);self.assertGreaterEqual(n.min(),2)
        with self.assertRaises(ValueError):e.allocation([0,0],[1,1],3)

    def test_confidence_edges(self):
        values=e.lower_squared_sum(np.array([[0],[100],[50]]),[100],[1],.01)
        self.assertAlmostEqual(values[0],values[1],places=10)
        self.assertEqual(values[2],0)
        self.assertTrue(0<values[0]<1)

    def test_corrupted_state_rejected(self):
        with self.assertRaises(ValueError):e.density_channel(np.array([1,1]),1,'none',0)

    def test_negative_control(self):
        s=e.system('C009')
        self.assertEqual(s['bound'],3)
        for k in range(5):
            psi=self.state(s['qubits'],k)
            mu=e.density_expectations(e.density_channel(psi,s['qubits'],'amplitude_damping',.1),s['labels'])
            self.assertLessEqual(np.array(s['weights'])@mu**2,3+1e-10)

    def test_schedule(self):
        from run_campaign import jobs
        plan=jobs()
        self.assertEqual(len(plan),720)
        self.assertEqual(len({(x['graph'],x['frame'],x['noise'],x['rep']) for x in plan}),720)


if __name__ == '__main__':unittest.main()
