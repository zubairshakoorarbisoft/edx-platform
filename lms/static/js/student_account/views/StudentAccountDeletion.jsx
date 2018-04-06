import React, { Component } from 'react';
import { Button } from '@edx/paragon';

class StudentAccountDeletion extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        <h2>Delete My Account</h2>
        <span>We're sorry to see you go!</span>
        <span>Please note:</span>
        <span>If your account is deleted, ALL your data will be deleted. This includes:</span>
        <ul>
          <li>Credentials</li>
          <li>Certificates</li>
          <li>Program and Course data</li>
          <li>Profile data</li>
        </ul>
        <span>You will not be able to make a new account on edX with the same email address</span>
        <Button label="Delete My Account" />
      </div>
    )
  }
}
