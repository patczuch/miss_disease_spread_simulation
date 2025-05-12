import pygame
import sys
import numpy as np
import datetime
from enum import Enum
import csv
import argparse

# global settings
boundary = None
mortality_rate = None
death_time = None
susceptible_again_time = None
n_susceptible = None
n_infected = None
n_recovered = None
person_size = None
recovered_enabled = None  # SIS / SIRS switch
fast_mode = None


class Color(Enum):
    GREEN = (50, 150, 50)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)


class PersonState(Enum):
    SUSCEPTIBLE = 1
    INFECTED = 2
    RECOVERED = 3
    DEAD = 4


class Person(pygame.sprite.Sprite):
    def __init__(self, pos, state):
        super().__init__()

        self.image = pygame.Surface([person_size, person_size], pygame.SRCALPHA)

        self.pos = pos
        self.state = state

        self.vel = [0, 0]
        self.rect = self.image.get_rect()

        self.death_timer = death_time

        self.susceptible_again_timer = susceptible_again_time

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        if self.pos[0] < 0:
            self.pos[0] = 0
        elif self.pos[0] > boundary[0] - person_size:
            self.pos[0] = boundary[0] - person_size

        if self.pos[1] < 0:
            self.pos[1] = 0
        elif self.pos[1] > boundary[1] - person_size:
            self.pos[1] = boundary[1] - person_size

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

        vel_norm = np.linalg.norm(self.vel)
        if vel_norm > 3:
            self.vel /= vel_norm
        self.vel += np.random.rand(2) * 2 - 1

        if self.state == PersonState.INFECTED:
            self.death_timer -= 1
            if self.death_timer <= 0:
                if mortality_rate > np.random.rand():
                    self.state = PersonState.DEAD
                else:
                    if recovered_enabled:
                        self.state = PersonState.RECOVERED
                    else:
                        self.state = PersonState.SUSCEPTIBLE
                    self.death_timer = death_time

        if self.state == PersonState.RECOVERED:
            self.susceptible_again_timer -= 1
            if self.susceptible_again_timer <= 0:
                self.state = PersonState.SUSCEPTIBLE
                self.susceptible_again_timer = susceptible_again_time

    def render(self):
        color = Color.WHITE
        if self.state == PersonState.SUSCEPTIBLE:
            color = Color.GREEN
        elif self.state == PersonState.INFECTED:
            color = Color.RED
        elif self.state == PersonState.RECOVERED:
            color = Color.BLUE

        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image, color.value, (10, 10), 10
        )


class Simulation:
    def __init__(self):
        self.people = []

    def spawn_random_person(self, state):
        self.people.append(Person([np.random.randint(0, boundary[0] - person_size),
                                   np.random.randint(0, boundary[1] - person_size)], state))

    def start(self):

        pygame.init()

        screen = pygame.display.set_mode(boundary)

        for _ in range(n_susceptible):
            self.spawn_random_person(PersonState.SUSCEPTIBLE)

        for _ in range(n_infected):
            self.spawn_random_person(PersonState.INFECTED)

        if recovered_enabled:
            for _ in range(n_recovered):
                self.spawn_random_person(PersonState.RECOVERED)

        clock = pygame.time.Clock()

        d = datetime.datetime.now()

        csvfile = open('simulation_stats-{date:%Y-%m-%d_%H_%M_%S}.csv'.format(date=d), 'w', newline='')
        writer = csv.writer(csvfile)
        writer.writerow(['frame', 'susceptible', 'infected', 'recovered', 'dead_this_frame', 'total_deaths'])

        parametersfile = open('simulation_parameters-{date:%Y-%m-%d_%H_%M_%S}.txt'.format(date=d), 'w', newline='')
        parametersfile.write("boundary " + str(boundary) +
                            "\nmortality_rate " + str(mortality_rate) +
                            "\ndeath_time " + str(death_time) +
                            "\nsusceptible_again_time " + str(susceptible_again_time) +
                            "\nn_susceptible " + str(n_susceptible) +
                            "\nn_infected " + str(n_infected) +
                            "\nn_recovered " + str(n_recovered) +
                            "\nperson_size " + str(person_size) +
                            "\nrecovered_enabled " + str(recovered_enabled) +
                            "\nfast_mode " + str(fast_mode))
        frame_count = 0
        total_deaths = 0
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        sys.exit()

                # Update people
                for person in self.people:
                    person.update()

                prev_count = len(self.people)
                self.people = [person for person in self.people if person.state != PersonState.DEAD]
                dead_this_frame = prev_count - len(self.people)
                total_deaths += dead_this_frame

                susceptible = 0
                infected = 0
                recovered = 0

                for person in self.people:
                    if person.state == PersonState.SUSCEPTIBLE:
                        susceptible += 1
                    elif person.state == PersonState.INFECTED:
                        infected += 1
                    elif person.state == PersonState.RECOVERED:
                        recovered += 1

                writer.writerow([frame_count, susceptible, infected, recovered, dead_this_frame, total_deaths])
                csvfile.flush()
                frame_count += 1

                # Check for collisions
                for person1 in self.people:
                    for person2 in self.people:
                        if pygame.sprite.collide_rect(person1, person2):
                            if person1.state == PersonState.INFECTED and person2.state == PersonState.SUSCEPTIBLE:
                                person2.state = PersonState.INFECTED

                screen.fill(Color.WHITE.value)

                # Draw people
                for person in self.people:
                    person.render()
                    screen.blit(person.image, person.rect)

                if not fast_mode:
                    clock.tick(30)
                pygame.display.flip()
        finally:
            parametersfile.close()
            csvfile.close()
            pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulation Configuration")

    parser.add_argument("--boundary", nargs=2, type=int, default=[600, 600], help="Simulation boundary as width height")
    parser.add_argument("--mortality_rate", type=float, default=0.5, help="Mortality rate (0.0 to 1.0)")
    parser.add_argument("--death_time", type=int, default=300, help="Time until death for infected individuals")
    parser.add_argument("--susceptible_again_time", type=int, default=300,
                        help="Time after which recovered become susceptible")
    parser.add_argument("--n_susceptible", type=int, default=40, help="Initial number of susceptible individuals")
    parser.add_argument("--n_infected", type=int, default=10, help="Initial number of infected individuals")
    parser.add_argument("--n_recovered", type=int, default=3, help="Initial number of recovered individuals")
    parser.add_argument("--person_size", type=int, default=20, help="Size of each person in the simulation")
    parser.add_argument("--recovered_enabled", type=bool, default=True,
                        help="Enable recovered state (True for SIRS, False for SIS)")
    parser.add_argument("--fast_mode", type=bool, default=True, help="Enable fast mode")

    args = parser.parse_args()

    boundary = args.boundary
    mortality_rate = args.mortality_rate
    death_time = args.death_time
    susceptible_again_time = args.susceptible_again_time
    n_susceptible = args.n_susceptible
    n_infected = args.n_infected
    n_recovered = args.n_recovered
    person_size = args.person_size
    recovered_enabled = args.recovered_enabled
    fast_mode = args.fast_mode

    Simulation().start()
