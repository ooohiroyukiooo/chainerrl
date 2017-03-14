from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import *  # NOQA
from future import standard_library
standard_library.install_aliases()
import os
import tempfile
import unittest

from chainerrl import replay_buffer


class TestReplayBuffer(unittest.TestCase):

    def test_append_and_sample(self):
        rbuf = replay_buffer.ReplayBuffer(100)

        self.assertEqual(len(rbuf), 0)

        # Add one and sample one
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        self.assertEqual(len(rbuf), 1)
        s1 = rbuf.sample(1)
        self.assertEqual(len(s1), 1)
        self.assertEqual(s1[0], trans1)

        # Add two and sample two, which must be unique
        trans2 = dict(state=1, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans2)
        self.assertEqual(len(rbuf), 2)
        s2 = rbuf.sample(2)
        self.assertEqual(len(s2), 2)
        if s2[0]['state'] == 0:
            self.assertEqual(s2[0], trans1)
            self.assertEqual(s2[1], trans2)
        else:
            self.assertEqual(s2[0], trans2)
            self.assertEqual(s2[1], trans1)

    def test_save_and_load(self):

        tempdir = tempfile.mkdtemp()

        rbuf = replay_buffer.ReplayBuffer(100)

        # Add two transitions
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        trans2 = dict(state=1, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans2)

        # Now it has two transitions
        self.assertEqual(len(rbuf), 2)

        # Save
        filename = os.path.join(tempdir, 'rbuf.pkl')
        rbuf.save(filename)

        # Initialize rbuf
        rbuf = replay_buffer.ReplayBuffer(100)

        # Of course it has no transition yet
        self.assertEqual(len(rbuf), 0)

        # Load the previously saved buffer
        rbuf.load(filename)

        # Now it has two transitions again
        self.assertEqual(len(rbuf), 2)

        # And sampled transitions are exactly what I added!
        s2 = rbuf.sample(2)
        if s2[0]['state'] == 0:
            self.assertEqual(s2[0], trans1)
            self.assertEqual(s2[1], trans2)
        else:
            self.assertEqual(s2[0], trans2)
            self.assertEqual(s2[1], trans1)


class TestPrioritizedReplayBuffer(unittest.TestCase):

    def test_append_and_sample(self):
        rbuf = replay_buffer.PrioritizedReplayBuffer(100)

        self.assertEqual(len(rbuf), 0)

        # Add one and sample one
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        self.assertEqual(len(rbuf), 1)
        s1 = rbuf.sample(1)
        rbuf.update_errors([3.14])
        self.assertEqual(len(s1), 1)
        self.assertAlmostEqual(s1[0]['weight'], 1.0)
        del s1[0]['weight']
        self.assertEqual(s1[0], trans1)

        # Add two and sample two, which must be unique
        trans2 = dict(state=1, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans2)
        self.assertEqual(len(rbuf), 2)
        s2 = rbuf.sample(2)
        rbuf.update_errors([3.14, 2.71])
        self.assertEqual(len(s2), 2)
        del s2[0]['weight']
        del s2[1]['weight']
        if s2[0]['state'] == 0:
            self.assertEqual(s2[0], trans1)
            self.assertEqual(s2[1], trans2)
        else:
            self.assertEqual(s2[0], trans2)
            self.assertEqual(s2[1], trans1)

        # Weights should be different for different TD-errors
        s3 = rbuf.sample(2)
        self.assertNotAlmostEqual(s3[0]['weight'], s3[1]['weight'])
        rbuf.update_errors([3.14, 3.14])

        # Weights should be equal for the same TD-errors
        s4 = rbuf.sample(2)
        self.assertAlmostEqual(s4[0]['weight'], s4[1]['weight'])

    @unittest.expectedFailure
    def test_fail_noupdate(self):
        rbuf = replay_buffer.PrioritizedReplayBuffer(100)
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        rbuf.sample(1)
        rbuf.sample(1)  # This line must fail.

    def test_fail_noupdate_sub(self):
        rbuf = replay_buffer.PrioritizedReplayBuffer(100)
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        rbuf.sample(1)
        # This must not fail.

    def test_save_and_load(self):

        tempdir = tempfile.mkdtemp()

        rbuf = replay_buffer.PrioritizedReplayBuffer(100)

        # Add two transitions
        trans1 = dict(state=0, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans1)
        trans2 = dict(state=1, action=1, reward=2, next_state=3,
                      next_action=4, is_state_terminal=True)
        rbuf.append(**trans2)

        # Now it has two transitions
        self.assertEqual(len(rbuf), 2)

        # Save
        filename = os.path.join(tempdir, 'rbuf.pkl')
        rbuf.save(filename)

        # Initialize rbuf
        rbuf = replay_buffer.PrioritizedReplayBuffer(100)

        # Of course it has no transition yet
        self.assertEqual(len(rbuf), 0)

        # Load the previously saved buffer
        rbuf.load(filename)

        # Now it has two transitions again
        self.assertEqual(len(rbuf), 2)

        # And sampled transitions are exactly what I added!
        s2 = rbuf.sample(2)
        del s2[0]['weight']
        del s2[1]['weight']
        if s2[0]['state'] == 0:
            self.assertEqual(s2[0], trans1)
            self.assertEqual(s2[1], trans2)
        else:
            self.assertEqual(s2[0], trans2)
            self.assertEqual(s2[1], trans1)
