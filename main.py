import pygame, sys
import numpy as np
from enum import Enum

# global settings
boundary = [600, 600]
mortality_rate = 0.5
death_time = 300
n_healthy = 40
n_infected = 10
n_recovered = 3

person_size = 20


class Color(Enum):
    GREEN = (50, 150, 50)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    WHITE = (255, 255, 255)


class PersonState(Enum):
    HEALTHY = 1
    SICK = 2
    RECOVERED = 3
    DEAD = 4


class Person(pygame.sprite.Sprite):
    def __init__(self, pos, state):
        super().__init__()

        global person_size
        self.image = pygame.Surface([person_size, person_size], pygame.SRCALPHA)

        self.pos = pos
        self.state = state

        self.vel = [0, 0]
        self.rect = self.image.get_rect()

        global death_time
        self.death_timer = death_time

    def update(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        global boundary

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

        if self.state == PersonState.SICK:
            self.death_timer -= 1
            if self.death_timer <= 0:
                global mortality_rate
                if mortality_rate > np.random.rand():
                    self.state = PersonState.DEAD
                else:
                    self.state = PersonState.RECOVERED

    def render(self):
        color = Color.WHITE
        if self.state == PersonState.HEALTHY:
            color = Color.GREEN
        elif self.state == PersonState.SICK:
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
        global boundary
        global person_size
        self.people.append(Person([np.random.randint(0, boundary[0] - person_size),
                                   np.random.randint(0, boundary[1] - person_size)], state))

    def start(self):

        pygame.init()

        global boundary
        screen = pygame.display.set_mode(boundary)

        global n_healthy
        for _ in range(n_healthy):
            self.spawn_random_person(PersonState.HEALTHY)

        global n_infected
        for _ in range(n_infected):
            self.spawn_random_person(PersonState.SICK)

        global n_recovered
        for _ in range(n_recovered):
            self.spawn_random_person(PersonState.RECOVERED)

        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            # Update people
            for person in self.people:
                person.update()

            self.people = [person for person in self.people if person.state != PersonState.DEAD]


            # Check for collisions
            for person1 in self.people:
                for person2 in self.people:
                    if pygame.sprite.collide_rect(person1, person2):
                        if person1.state == PersonState.SICK and person2.state == PersonState.HEALTHY:
                            person2.state = PersonState.SICK

            screen.fill(Color.WHITE.value)

            # Draw people
            for person in self.people:
                person.render()
                screen.blit(person.image, person.rect)

            clock.tick(30)
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    Simulation().start()